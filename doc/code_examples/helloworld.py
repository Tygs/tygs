#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tygs import App

app = App()

@app.route("/")
def index(req, res):
    res.write("Hello, world")

@app.route("/json")
def json(req, res):
    res.json({"Hello": "world"})

@app.route("/text")
def text(req, res):
    res.text("Hello, world")

app.run()
