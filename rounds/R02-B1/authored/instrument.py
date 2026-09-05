#!/usr/bin/env python3
"""instrument — the read-only herdr unix-socket adapter (R02 · B1).

One chokepoint: every request travels through ``Instrument.call()``, which
enforces a frozen read-only method allowlist (``READ_ONLY_METHODS``)
*before* any byte is written to the socket — a non-allowlisted method
raises ``MethodNotAllowedError`` and the socket is never even connected.

Facts this adapter encodes (commission §3.1, probed on the live box —
stated here, not re-derived):

  * request envelope ``{"id", "method", "params"}`` — all three required,
    one JSON object per line, ``\\n``-framed;
  * response: one ``\\n``-framed line; success carries ``result``, failure
    carries ``error`` = ``{"code", "message"}`` (structured errors are
    mapped to typed exceptions, code by code);
  * every result is a tagged union keyed by ``type`` with the payload
    under a method-specific key (``pane_read`` → ``read``, ``pane_list`` →
    ``panes``, ``pane_info`` → ``pane``, ``agent_info`` → ``agent``, …);
    this adapter unwraps the method-specific key so callers never see the
    envelope;
  * desks are resolved by pane *label* on every use — a remembered
    pane_id is never trusted (pane ids are volatile: the live box reads
    ``w2:*`` on disk and ``w8:*`` live, §3.2);
  * after a socket error the connection is dropped, reconnected, and the
    request retried once; desk resolution re-derives ids from labels, so
    re-minted ids are picked up instead of being remembered (C4).

The adapter performs no pane writes of any kind: only the methods of the
read-only allowlist can reach the socket, and this module itself only
sends reads.  The §5.1 forbidden write-method list appears nowhere here,
by name or by call — the allowlist is the enforcement (C3).
"""

from __future__ import annotations

import itertools
import json
import os
import socket

__all__ = [
    "Instrument",
    "READ_ONLY_METHODS",
    "DESK_LABELS",
    "PANE_READ_FIELDS",
    "HerdrError",
    "MethodNotAllowedError",
    "HerdrProtocolError",
    "SocketTransportError",
    "HerdrRemoteError",
    "PaneNotFoundError",
    "AgentNotFoundError",
    "DeskResolutionError",
]

# The frozen read-only allowlist (commission §3.1): the only methods this
# round may touch.  Instrument.call() — the single chokepoint — enforces it.
READ_ONLY_METHODS = frozenset((
    "ping",
    "pane.list",
    "pane.get",
    "pane.read",
    "pane.process_info",
    "pane.current",
    "pane.layout",
    "pane.edges",
    "pane.neighbor",
    "agent.list",
    "agent.get",
    "agent.read",
    "tab.list",
    "workspace.list",
    "session.snapshot",
    "events.subscribe",
    "events.wait",
    "pane.wait_for_output",
))

# Tagged-union unwrapping (§3.1): the result payload sits under a
# method-specific key.  Methods without a specific key return the whole
# result object (their ``type`` field is the payload itself, e.g. ping).
_RESULT_KEYS = {
    "pane.list": "panes",
    "pane.get": "pane",
    "pane.read": "read",
    "agent.list": "agents",
    "agent.get": "agent",
    "agent.read": "read",
    "pane.current": "pane",
    "pane.process_info": "process_info",
    "session.snapshot": "snapshot",
}

# The label → desk map is DATA — one config table, one place to change
# (commission §3.2 fact 4).  Labels are presentation and may be renamed at
# will; the desk keys — and everything a record means — never change with
# a relabel.  Defaults are the live labels of §3.2 (centre = S).
DESK_LABELS = {
    "podium": "S",
    "G": "G",
    "Q": "Q",
    "P": "P",
    "V": "V",
}

# All eight fields a well-formed PaneReadResult must carry (§3.1).
PANE_READ_FIELDS = (
    "pane_id", "workspace_id", "tab_id", "source",
    "format", "text", "truncated", "revision",
)

_DEFAULT_SOCKET_PATH = os.path.expanduser("~/.config/herdr/herdr.sock")


class HerdrError(Exception):
    """Base class for every adapter error.  Failures are typed, never silent."""


class MethodNotAllowedError(HerdrError):
    """The chokepoint refused a method not in READ_ONLY_METHODS, before any
    byte reached the socket (C3)."""

    def __init__(self, method):
        self.method = method
        super().__init__(
            "method %r is not in READ_ONLY_METHODS; nothing was sent"
            % (method,))


class HerdrProtocolError(HerdrError):
    """The server's bytes do not match the framed JSON contract of §3.1."""


class SocketTransportError(HerdrError):
    """The unix socket could not be used after the reconnect attempt(s)."""

    def __init__(self, message, cause=None):
        self.cause = cause
        super().__init__(message)


class HerdrRemoteError(HerdrError):
    """A structured {"code","message"} error returned by the server."""

    def __init__(self, code, message, method=None):
        self.code = code
        self.message = message
        self.method = method
        super().__init__(
            "herdr error %r on %r: %s" % (code, method, message))


class PaneNotFoundError(HerdrRemoteError):
    """The server answered pane_not_found for the requested pane_id."""


class AgentNotFoundError(HerdrRemoteError):
    """The server answered agent_not_found for the requested target."""


class DeskResolutionError(HerdrError):
    """A desk key could not be resolved to a pane by label."""


_ERROR_TYPES = {
    "pane_not_found": PaneNotFoundError,
    "agent_not_found": AgentNotFoundError,
}


class Instrument:
    """A raw herdr unix-socket client with a read-only chokepoint.

    Constructed with a socket path (any AF_UNIX path — this is how it is
    tested) and nothing global::

        Instrument(socket_path="/tmp/.../herdr.sock")

    With no path, the env var HERDR_SOCKET_PATH is consulted, then the
    default live path (§3.1) — every test and the verifier pass a scratch
    path explicitly.

    Every call goes through ``call()``.  This class never remembers a
    pane_id: ``desks()`` re-resolves desk keys from pane labels on every
    use, and after a socket error the connection is reconnected and the
    labels are resolved again.
    """

    def __init__(self, socket_path=None, timeout_s=15.0, retries=1,
                 desk_labels=None):
        self.socket_path = (
            socket_path
            or os.environ.get("HERDR_SOCKET_PATH")
            or _DEFAULT_SOCKET_PATH)
        self.timeout_s = float(timeout_s)
        self.retries = int(retries)
        self.desk_labels = dict(
            desk_labels if desk_labels is not None else DESK_LABELS)
        self._sock = None
        self._inbuf = bytearray()
        self._ids = itertools.count(1)
        self.reconnects = 0
        self._closed = False

    # -- connection plumbing --------------------------------------------

    def _connect(self):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout_s)
        sock.connect(self.socket_path)
        self._sock = sock
        self._inbuf = bytearray()

    def _drop(self):
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = None
        self._inbuf = bytearray()

    def close(self):
        self._drop()
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def _read_line(self):
        while True:
            idx = self._inbuf.find(b"\n")
            if idx != -1:
                line = bytes(self._inbuf[:idx])
                del self._inbuf[:idx + 1]
                return line
            chunk = self._sock.recv(65536)
            if not chunk:
                raise EOFError("connection closed by server")
            self._inbuf += chunk

    # -- the single chokepoint -------------------------------------------

    def call(self, method, params=None):
        """call(method, params) -> the unwrapped result payload.

        The single chokepoint.  The allowlist is enforced *first*: a
        method outside READ_ONLY_METHODS raises MethodNotAllowedError
        before any byte reaches the socket (C3).  Success returns the
        tagged-union payload unwrapped from its method-specific key
        (§3.1); a structured error becomes a typed exception; a socket
        error drops the connection, reconnects, and retries once (C4).
        """
        if method not in READ_ONLY_METHODS:
            raise MethodNotAllowedError(method)
        params = {} if params is None else params
        if not isinstance(params, dict):
            raise HerdrProtocolError(
                "params must be a JSON object, got %s"
                % type(params).__name__)
        if self._closed:
            raise HerdrError("instrument is closed")
        last_cause = None
        for _attempt in range(self.retries + 1):
            request_id = str(next(self._ids))
            try:
                if self._sock is None:
                    self._connect()
                envelope = {"id": request_id, "method": method,
                            "params": params}
                line = json.dumps(
                    envelope, ensure_ascii=False, allow_nan=False,
                ).encode("utf-8") + b"\n"
                self._sock.sendall(line)
                raw = self._read_line()
                return self._decode(raw, method, request_id)
            except socket.timeout as exc:
                # A timeout is a hung server, not a restart: retrying would
                # stall the field for another full timeout, so it raises
                # now, bounded.  The connection is dropped; the next call
                # reconnects fresh.
                self._drop()
                raise SocketTransportError(
                    "timed out after %.1fs on %r"
                    % (self.timeout_s, method), cause=exc) from exc
            except (OSError, EOFError) as exc:
                # Server restart / dropped connection (C4): reconnect and
                # retry the request; desk resolution re-derives ids from
                # labels on the next use.
                self._drop()
                self.reconnects += 1
                last_cause = exc
        raise SocketTransportError(
            "socket failed on %r after %d reconnect attempt(s): %r"
            % (method, self.retries, last_cause), cause=last_cause)

    def _decode(self, raw, method, request_id):
        try:
            obj = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HerdrProtocolError(
                "response line is not JSON (%s)" % exc) from exc
        if not isinstance(obj, dict):
            raise HerdrProtocolError("response is not a JSON object")
        if obj.get("id") != request_id:
            raise HerdrProtocolError(
                "response id %r does not echo request id %r"
                % (obj.get("id"), request_id))
        if "error" in obj:
            err = obj["error"]
            if (not isinstance(err, dict)
                    or not isinstance(err.get("code"), str)
                    or not isinstance(err.get("message"), str)):
                raise HerdrProtocolError(
                    "structured error must carry string code and message")
            raise _ERROR_TYPES.get(err["code"], HerdrRemoteError)(
                err["code"], err["message"], method)
        if "result" not in obj:
            raise HerdrProtocolError(
                "response carries neither result nor error")
        result = obj["result"]
        if not isinstance(result, dict):
            raise HerdrProtocolError(
                "result payload is not a JSON object: %s"
                % type(result).__name__)
        key = _RESULT_KEYS.get(method)
        if key is not None:
            if key not in result:
                raise HerdrProtocolError(
                    "%s response missing %r payload" % (method, key))
            return result[key]
        return result

    # -- read-only convenience surface -----------------------------------

    def ping(self):
        return self.call("ping", {})

    def panes(self, workspace_id=None):
        params = {} if workspace_id is None else {"workspace_id": workspace_id}
        return self.call("pane.list", params)

    def pane_info(self, pane_id):
        return self.call("pane.get", {"pane_id": pane_id})

    def agent_info(self, target):
        """agent.get takes ``target`` — and target is a pane_id (§3.1 trap)."""
        return self.call("agent.get", {"target": target})

    def _read_pane_dict(self, pane_id, source="visible", lines=None,
                        strip_ansi=True, fmt="text"):
        params = {
            "pane_id": pane_id,
            "source": source,
            "format": fmt,
            "strip_ansi": strip_ansi,
        }
        if lines is not None:
            params["lines"] = lines
        read = self.call("pane.read", params)
        if not isinstance(read, dict):
            raise HerdrProtocolError("pane.read payload is not an object")
        missing = [field for field in PANE_READ_FIELDS if field not in read]
        if missing:
            raise HerdrProtocolError(
                "PaneReadResult missing field(s): %s"
                % ", ".join(missing))
        if not isinstance(read["truncated"], bool):
            raise HerdrProtocolError(
                "PaneReadResult.truncated is not a bool")
        return read

    def read_pane(self, pane_id=None, desk=None, source="visible",
                  lines=None, strip_ansi=True, fmt="text"):
        """read_pane -> the unwrapped PaneReadResult dict (all eight fields).

        When ``desk=`` is given, the pane_id is resolved by label on THIS
        call — never from a remembered id."""
        if desk is not None:
            pane_id = self.desks()[desk]
        if pane_id is None:
            raise HerdrError("read_pane needs pane_id= or desk=")
        return self._read_pane_dict(
            pane_id, source=source, lines=lines, strip_ansi=strip_ansi,
            fmt=fmt)

    # -- label-resolved desk surface -------------------------------------

    def _resolve(self):
        """Resolve desk keys from pane labels on THIS call.

        Rules (commission §3.2): only panes whose label is a key of the
        label→desk config table are desks (a null label is never indexed);
        the cell's own workspace is derived from the labels resolved — the
        workspace holding the most desk panes — never from an assumed
        workspace id; a tie between workspaces, a duplicated desk in one
        workspace, or zero desk panes is an ambiguity and raises instead
        of guessing."""
        panes = self.call("pane.list", {})
        if not isinstance(panes, list):
            raise HerdrProtocolError(
                "pane_list payload 'panes' is not a list")
        by_workspace = {}
        for pane in panes:
            if not isinstance(pane, dict):
                raise HerdrProtocolError("pane_list entry is not an object")
            label = pane.get("label")
            if not isinstance(label, str) or label not in self.desk_labels:
                continue  # unlabelled or not a desk — never indexed
            ws = pane.get("workspace_id")
            pid = pane.get("pane_id")
            if (not isinstance(ws, str) or not ws
                    or not isinstance(pid, str) or not pid):
                raise HerdrProtocolError(
                    "desk pane %r missing workspace_id or pane_id"
                    % (label,))
            desk = self.desk_labels[label]
            by_workspace.setdefault(ws, {}).setdefault(desk, set()).add(pid)
        if not by_workspace:
            raise DeskResolutionError(
                "no pane carries any desk label from the config table")
        chosen = None
        best = -1
        ambiguous = False
        for ws, found in by_workspace.items():
            if len(found) > best:
                best, chosen, ambiguous = len(found), ws, False
            elif len(found) == best:
                ambiguous = True
        if ambiguous or chosen is None:
            raise DeskResolutionError(
                "desk labels are split across workspaces with equal "
                "counts; the arrangement is ambiguous")
        found = by_workspace[chosen]
        resolved = {}
        for desk in sorted(found):
            ids = found[desk]
            if len(ids) > 1:
                raise DeskResolutionError(
                    "desk %r resolves to more than one pane in workspace %r"
                    % (desk, chosen))
            resolved[desk] = next(iter(ids))
        return resolved

    def desks(self):
        """-> {desk_key: pane_id}, resolved by pane LABEL on this call.

        Never a remembered pane_id: every call re-resolves from a fresh
        pane.list (K1, C4)."""
        return self._resolve()

    def observe_desks(self, include_output=True):
        """One arrangement pass: resolve labels once, then observe every desk.

        Per desk: pane.get (PaneInfo.agent_status is a required field);
        agent.get for panes that carry an agent (the §4.4 herdr signal
        path, with target = pane_id per the §3.1 trap); pane.read for
        output.  Returns
        {"arrangement": {desk: {pane_id, workspace_id, label}},
         "desks": {desk: observed state}}."""
        resolved = self._resolve()
        desks = {}
        for desk in sorted(resolved):
            pane_id = resolved[desk]
            pane = self.call("pane.get", {"pane_id": pane_id})
            if not isinstance(pane, dict):
                raise HerdrProtocolError(
                    "pane_info payload for %r is not an object" % (pane_id,))
            if not isinstance(pane.get("agent_status"), str):
                raise HerdrProtocolError(
                    "PaneInfo.agent_status missing or not a string for "
                    "pane %r" % (pane_id,))
            label = pane.get("label")
            if not isinstance(label, str):
                label = self._label_for(desk)
            state = {
                "pane_id": pane_id,
                "workspace_id": pane.get("workspace_id"),
                "label": label,
                "agent_status": pane.get("agent_status"),
                "agent_status_source": "pane.get",
                "agent": pane.get("agent"),
                "agent_get_error": None,
                "focused": pane.get("focused"),
                "revision_pane_info": pane.get("revision"),
            }
            if pane.get("agent"):
                try:
                    agent = self.call("agent.get", {"target": pane_id})
                    if not isinstance(agent, dict):
                        raise HerdrProtocolError(
                            "agent_info payload for %r is not an object"
                            % (pane_id,))
                    if not isinstance(agent.get("agent_status"), str):
                        raise HerdrProtocolError(
                            "AgentInfo.agent_status missing or not a string "
                            "for %r" % (pane_id,))
                    state["agent_status"] = agent["agent_status"]
                    state["agent_status_source"] = "agent.get"
                except AgentNotFoundError as exc:
                    state["agent_get_error"] = exc.code
            if include_output:
                state["read"] = self._read_pane_dict(pane_id)
            desks[desk] = state
        arrangement = {}
        for desk, pane_id in resolved.items():
            arrangement[desk] = {
                "pane_id": pane_id,
                "workspace_id": desks[desk]["workspace_id"],
                "label": desks[desk]["label"],
            }
        return {"arrangement": arrangement, "desks": desks}

    def _label_for(self, desk):
        for label, key in self.desk_labels.items():
            if key == desk:
                return label
        return None

    def desk_states(self):
        """-> {desk_key: observed state incl. agent_status}, label-resolved
        on this call."""
        return self.observe_desks(include_output=False)["desks"]
