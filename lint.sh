#!/bin/bash

black --exclude "/migrations/" hmt_cite_atlas
isort -rc hmt_cite_atlas
flake8 hmt_cite_atlas
