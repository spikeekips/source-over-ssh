# -*- coding: utf-8 -*-

import ConfigParser
import hashlib
import re
from StringIO import StringIO

import utils


class ConfigDatabase (object, ) :
    """
    Read/Handle config database.

    """

    default_repository = {
        "description": None,
        "path": None,
        "password": None,
    }

    default_user = {
        "public_key": None,
        "password": None,
        "realname": None,
        "email": None,
        "admin": None,
        "repository": None,
    }
    datatype_user = {
        "repository": "list",
    }
    datatype_repository = {
        "port": "int",
    }

    @classmethod
    def from_filename (cls, filename, *a, **kw) :
        return cls(file(filename, ), *a, **kw)

    @classmethod
    def from_string (cls, s, *a, **kw) :
        return cls(StringIO(s, ), *a, **kw)

    def __init__ (self, fp, _global=False, ) :
        self._fp = fp
        self._global = _global
        self._config = ConfigParser.ConfigParser()
        self._config.readfp(fp, )

        self._parse()

    @property
    def raw_config (self, ) :
        _s = StringIO()
        self.save(_s, )

        _s.seek(0, 0, )
        return _s.getvalue()

    def rename_section (self, old, new, ) :
        if old == new :
            return

        if not self._config.has_section(old, ) :
            raise KeyError("'%s' does not exist." % old, )

        self._config.add_section(new, )
        for i, j in self._config.items(old, ) :
            self._config.set(new, i, j, )

        self._config.remove_section(old, )

        return self

    def _parse (self, ) :
        pass

    def save (self, fp=None, ) :
        _save_original = not bool(fp, )
        if _save_original :
            fp = StringIO()

        self._config.write(fp, )

        fp.seek(0, 0, )

        if _save_original :
            if isinstance(self._fp, StringIO, ) :
                self._fp.close()

                self._fp = fp
            else :
                _fd = file(self._fp.name, "w", )
                _fd.write(fp.getvalue(), )
                _fd.close()

                self._fp = file(self._fp.name, )

        return self

    def _parse_section (self, s, skel, ) :
        _d = skel.copy()
        for i in _d.keys() :
            try :
                _v = self._config.get(s, i, )
            except :
                _v = None

            _d[i] = _v

        return {s: _d, }

    def to_config_properties (self, skel=None, datatype=None, **properties) :
        if datatype is None :
            datatype = dict()

        for i, j in properties.items() :
            _datatype = datatype.get(i, "str", )
            if skel and i not in skel :
                continue
            elif j and _datatype == "list" :
                j = ", ".join(j)
            elif j and _datatype == "str" :
                j = str(j)

            yield (i, j, )

    def to_python_properties (self, datatype=None, **properties) :
        if datatype is None :
            datatype = dict()

        for i, j in properties.items() :
            _datatype = datatype.get(i, "str", )
            if _datatype == "list" :
                if not j :
                    j = list()
                else :
                    j = [k.strip() for k in j.split(",") if k.strip()]
            elif j and _datatype == "int" :
                j = int(j)
            elif j and _datatype == "long" :
                j = long(j)
            elif j and _datatype == "float" :
                j = float(j)

            yield (i, j, )

    ##################################################
    # user
    def _u(self, username, ) :
        return "user:%s" % username

    RE_USERNAME = re.compile("^user\:")

    def _ur (self, section, ) :
        return self.RE_USERNAME.sub("", section, )

    @property
    def users (self, ) :
        return [self._ur(i) for i in self._config.sections()
                if i.startswith("user:")]

    def has_user (self, username, ) :
        return self._config.has_section(self._u(username), )

    def get_user_property (self, username, p, default=None, ) :
        if not self.has_user(username, ) :
            raise KeyError("'%s' does not exist." % username, )

        if p not in self.default_user :
            raise KeyError("'%s' does not exist." % p, )

        if self._global and p == "repository" :
            return self.repositories

        try :
            _r = self._config.get(self._u(username), p, )
        except :
            return default

        return list(self.to_python_properties(
                datatype=self.datatype_user, **{p: _r, }))[0][1]

    def get_full_username (self, username, full=True, ) :
        _realname = self.get_user_property(username, "realname", )
        _email = self.get_user_property(username, "email", )
        if not _realname :
            _realname = username

        if not full :
            return _realname

        return "%s%s" % (
            _email and ("\"%s\"" % _realname) or _realname,
            _email and (" <%s>" % _email) or "",
        )

    def add_user (self, username, **properties) :
        if self.has_user(username, ) :
            raise KeyError("'%s' already exists." % username, )

        self._config.add_section(self._u(username), )

        for i, j in self.to_config_properties(
                self.default_user,
                datatype=self.datatype_user,
                **properties) :
            if i == "password" and j :
                j = self.__class__.encrypt_password(j)

            self._config.set(self._u(username), i, j, )

        return self

    def update_user (self, username, **properties) :
        if not self.has_user(username, ) :
            raise KeyError("'%s' does not exist." % username, )

        for i, j in self.to_config_properties(
                self.default_user, datatype=self.datatype_user, **properties) :
            if j is None :
                self._config.remove_option(self._u(username), i, )
            else :
                if i == "password" :
                    j = self.__class__.encrypt_password(j)
                elif i == "repository" and type(j) in (list, tuple, ) :
                    j = ", ".join(j, )

                self._config.set(self._u(username), i, j, )

        return self

    def remove_user (self, username, ) :
        if not self._config.remove_section(self._u(username), ) :
            raise KeyError("'%s' does not exist." % username, )

        return self

    def rename_user (self, old, new, ) :
        if not self.has_user(old, ) :
            raise KeyError("'%s' does not exist." % old, )

        if self.has_user(new, ) :
            raise KeyError("'%s' alreay exists." % new, )

        return self.rename_section(self._u(old), self._u(new), )

    def is_admin (self, username, ) :
        try :
            return self._config.getboolean(self._u(username), "admin", )
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError, ) :
            return False

    def set_admin (self, username, v="on", ) :
        _f = self._config._boolean_states.get(v.lower(), False, )
        if not _f :
            self._config.remove_option(self._u(username), "admin", )
        else :
            self._config.set(self._u(username), "admin", "on", )

        return self

    def search_user (self, k, ) :
        for i in self.users :
            if k in i :
                yield i
            elif k in self.get_user_property(i, "realname", "", ).lower() :
                yield i
            elif k in self.get_user_property(i, "email", "", ).lower() :
                yield i
            elif k in self.get_user_property(i, "repository", "", ).lower() :
                yield i

    ##################################################
    # repository
    def _r (self, alias, ) :
        return "repository:%s" % alias

    RE_REPOSITORY = re.compile("^repository\:")

    def _rr (self, section, ) :
        return self.RE_REPOSITORY.sub("", section, )

    @property
    def repositories (self, ) :
        return [self._rr(i) for i in self._config.sections()
                if i.startswith("repository:")]

    def has_repository (self, alias=None, path=None, ) :
        if alias :
            return self._config.has_section(self._r(utils.normpath(alias, )), )
        elif path :
            path = utils.normpath(path, )
            for i in self.repositories :
                if self.get_repository_property(i, "path", "", ) == path :
                    return True

        return False

    def get_repository_property (self, alias, p, default=None, ) :
        if not self.has_repository(alias, ) :
            raise KeyError("'%s' does not exist." % alias, )

        if p not in self.default_repository :
            raise KeyError("'%s' does not exist." % p, )

        try :
            _r = self._config.get(self._r(utils.normpath(alias), ), p, )
        except :
            return default

        return list(self.to_python_properties(
            datatype=self.datatype_repository, **{p: _r, }))[0][1]

    def add_repository (self, path, alias, **properties) :
        if self.has_repository(alias, ) :
            raise KeyError("'%s' already exists." % alias, )

        self._config.add_section(self._r(alias), )

        if not utils.is_remote_repository_path(path, ) :
            path = utils.normpath(path, )

        properties["path"] = path
        if "description" in properties :
            properties["description"] = " ".join(
                    properties.get("description"), )

        for i, j in self.to_config_properties(
                self.default_repository, **properties) :
            self._config.set(self._r(alias), i, j, )

        return self

    def update_repository (self, alias, **properties) :
        if not self.has_repository(alias, ) :
            raise KeyError("'%s' does not exist." % alias, )

        for i, j in self.to_config_properties(
                self.default_repository, **properties) :
            if i == "path" and j :
                j = utils.normpath(j, )

            if j is None :
                self._config.remove_option(self._r(alias), i, )
            else :
                self._config.set(self._r(alias), i, j, )

        return self

    def remove_repository (self, alias, ) :
        if not self._config.remove_section(self._r(alias), ) :
            raise KeyError("'%s' does not exist." % alias, )

        # apply the changes to the `repository` property in user
        for _username in self.users :
            _l = self.get_user_property(_username, "repository", list(), )
            if alias not in _l :
                continue

            del _l[_l.index(alias, )]
            self.update_user(_username, repository=_l, )

        return self

    def rename_repository (self, old, new, ) :
        if not self.has_repository(old, ) :
            raise KeyError("'%s' does not exist." % old, )

        new = utils.normpath(new, )
        if self.has_repository(new, ) :
            raise KeyError("'%s' alreay exists." % new, )

        _r = self.rename_section(self._r(old), self._r(new), )

        # apply the changes to the `repository` property in user
        for _username in self.users :
            _l = self.get_user_property(_username, "repository", list(), )
            if old not in _l :
                continue

            _l[_l.index(old, )] = new
            self.update_user(_username, repository=_l, )

        return _r

    @classmethod
    def encrypt_password (cls, s, ) :
        return hashlib.sha1(s).hexdigest()

    def is_remote_repository (self, alias, ) :
        return utils.is_remote_repository_path(
                self.get_repository_property(alias, "path", ), )

    def parse_remote_repository (self, alias, ) :
        if not self.is_remote_repository(alias, ) :
            raise ValueError("'%s' is not remote repository path." % alias, )

        return utils.parse_remote_repository(self.get_repository_property(alias, "path", ), )


if __name__ == "__main__" :
    import doctest
    doctest.testmod()


