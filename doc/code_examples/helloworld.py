#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals, print_function

from tygs import App

app = App()

@app.route("/")
def index(req, res):
    res.write(b"Hello, world")

@app.route("/json/")
def json(req, res):
    res.json({"Hello": "world"})

@app.route("/text/")
def text(req, res):
    res.html("Hello, world")

app.run()
