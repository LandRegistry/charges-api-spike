from flask import Flask, render_template, request, url_for, json, redirect, session, g, flash
from flask.ext.login import login_user, logout_user, current_user, login_required, UserMixin
import ldap
from config import LDAPSRV


class User(UserMixin):

    # NOTE - id = racf, uid = user ID from DB

    def __init__(self, id=None, uid=None, username=None, realname=None, location=None, admin=None):
        self.id = id
        self.uid = uid
        self.username = username
        self.realname = realname
        self.admin = admin
        self.location = location

    def get_id(self):
        return self.id

    def get_uid(self):
        return self.uid

    def get_username(self):
        return self.username

    def get_realname(self):
        return self.realname

    def get_location(self):
        return self.location

    def get_admin(self):
        return self.admin


def ldap_validate(uid=None, name=None, passwd=None):
    ldap.set_option(ldap.OPT_REFERRALS, 0)
    conn = ldap.open(LDAPSRV)
    try:
        if name is not None and passwd is not None:
            conn.simple_bind_s(name + '@diti',passwd)
            conn.unbind()
            print 'Authenticated'
            return True
        else:
            print 'Signed Out'
            return False
    except:
        print 'Authentication Failure'
        return False