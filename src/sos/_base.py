# -*- coding: utf-8 -*-


class BaseSessionTunnel (object, ) :
    name = None

    def __init__ (self, session, commandline, ) :
        self._session = session
        self._commandline = commandline

        self._avatar = self._session.avatar
        self._config_db = self._session.avatar._config_db

        self._alias = None
        self._repo_server_base = None
        self._repo_client_base = None

        self._is_remote = False
        self._client = None

    def close (self, ) :
        if self._client :
            self._client.close()

    def get_exec (self, ) :
        return self.parse_exec()

    def to_server (self, data, ) :
        return self.parse_to_server(data, )

    def to_client (self, data, ) :
        return self.parse_to_client(data, )

    def to_client_extended (self, data, ) :
        return self.parse_to_client_extended(data, )

    def parse_exec (self, ) :
        return self._commandline

    def parse_to_server (self, data, ) :
        return data

    def parse_to_client (self, data, ) :
        return data

    def parse_to_client_extended (self, data, ) :
        return data


class SessionTunnel (BaseSessionTunnel, ) :
    name = "none"


def get_session_tunnel (name, default=None, ) :
    try :
        return getattr(
                __import__("sos._%s" % name, None, None, ["_%s" % name, ], ),
                "SessionTunnel", )
    except (ImportError, AttributeError, ) :
        import traceback
        traceback.print_exc()
        return default


