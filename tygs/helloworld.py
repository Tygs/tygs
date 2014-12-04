#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tygs import App

app = App()

@app.route("/")
def index(req, res):
    res.write("Hello, world")

app.run()
