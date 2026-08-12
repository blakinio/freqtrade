from __future__ import annotations

from pathlib import Path

source = Path("tools/agents/apply_1355_final_closeout_findings.py")
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"), {"__name__": "__main__"})

path = Path("ai_platform/portal/runtime_supervisor/transport.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "from concurrent.futures import Future, ThreadPoolExecutor\n",
    "from concurrent.futures import ThreadPoolExecutor\n",
    1,
)
start_marker = "    def serve_forever(self, *, stop_event: threading.Event | None = None) -> None:\n"
end_marker = "    @staticmethod\n    def _read_request(connection: socket.socket) -> bytes:\n"
if text.count(start_marker) != 1 or text.count(end_marker) != 1:
    raise SystemExit("generated transport markers are not unique")
start = text.index(start_marker)
end = text.index(end_marker)
replacement = '''    def serve_forever(self, *, stop_event: threading.Event | None = None) -> None:
        address_family = self._validate_socket_root()
        listener = socket.socket(address_family, socket.SOCK_STREAM)
        workers = ThreadPoolExecutor(
            max_workers=self._max_workers, thread_name_prefix="runtime-supervisor-uds"
        )
        inflight = threading.BoundedSemaphore(self._max_inflight_connections)
        bound_inode: int | None = None
        try:
            listener.bind(str(self._path))
            bound_inode = self._path.lstat().st_ino
            self._path.chmod(0o660)
            listener.listen(self._max_inflight_connections)
            listener.settimeout(ACCEPT_POLL_SECONDS)
            self._accept_loop(listener, workers, inflight, stop_event)
        finally:
            listener.close()
            workers.shutdown(wait=True, cancel_futures=True)
            self._unlink_owned_socket(bound_inode)

    def _validate_socket_root(self) -> int:
        if os.name != "posix":
            raise SupervisorTransportError("runtime supervisor UDS requires a POSIX host")
        self._approved_root.mkdir(parents=True, mode=0o750, exist_ok=True)
        root_stat = self._approved_root.lstat()
        if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
            raise SupervisorTransportError("approved socket root must be a real directory")
        effective_uid = getattr(os, "geteuid", lambda: root_stat.st_uid)()
        if root_stat.st_uid != effective_uid or root_stat.st_mode & 0o022:
            raise SupervisorTransportError("approved socket root has unsafe ownership or mode")
        if self._path.exists() or self._path.is_symlink():
            raise SupervisorTransportError("refusing to replace an existing socket path")
        address_family = getattr(socket, "AF_UNIX", None)
        if address_family is None:
            raise SupervisorTransportError("AF_UNIX is unavailable")
        return address_family

    def _accept_loop(
        self,
        listener: socket.socket,
        workers: ThreadPoolExecutor,
        inflight: threading.BoundedSemaphore,
        stop_event: threading.Event | None,
    ) -> None:
        while stop_event is None or not stop_event.is_set():
            self._dispatch_connection(listener, workers, inflight)

    def _dispatch_connection(
        self,
        listener: socket.socket,
        workers: ThreadPoolExecutor,
        inflight: threading.BoundedSemaphore,
    ) -> None:
        if not inflight.acquire(timeout=ACCEPT_POLL_SECONDS):
            return
        try:
            connection, _ = listener.accept()
        except TimeoutError:
            inflight.release()
            return
        except OSError:
            inflight.release()
            raise
        try:
            future = workers.submit(self._serve_connection, connection)
        except RuntimeError:
            connection.close()
            inflight.release()
            raise
        future.add_done_callback(lambda _future: inflight.release())

    def _serve_connection(self, connection: socket.socket) -> None:
        with connection:
            try:
                self.handle(connection)
            except (TimeoutError, BrokenPipeError, ConnectionError):
                return

    def _unlink_owned_socket(self, bound_inode: int | None) -> None:
        if bound_inode is None:
            return
        try:
            current = self._path.lstat()
            if stat.S_ISSOCK(current.st_mode) and current.st_ino == bound_inode:
                self._path.unlink()
        except FileNotFoundError:
            pass

'''
path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")
