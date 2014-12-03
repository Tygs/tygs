#!/usr/bin/env python
# coding: utf-8

from tygs import App

app = App()


@app.route("/")
# @app.route('/', method='get')
def index(handler):
    handler.write("Hello, world")

app.run()
