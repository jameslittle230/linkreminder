I listened to a talk by [Andy Matuschak](https://andymatuschak.org/) recently. He talked about a lot of things relating to his research around transformative tools for thought, but one thing that stuck in my brain was this sort of demo he gave. In this demo, he would write down a question, and then he would get reminded of that question with exponential backoff: the question would reappear in a few days, then again after a few more, then again after a few weeks, months, etc. This framework allowed him to revisit ideas in his daily writing and build up different reactions to the same question over time, which could then be compiled into a larger, more comprehensive artifact that answered that original question.

Here, I've made a script that you run every hour via a cron job. This script will find Pinboard articles you've saved and remind you of them, with exponential backoff, letting you explore the links you've saved and maybe have reactions to them over the course of years.

## Setup

This project requires Python 3.

Install the [AWS CLI](https://aws.amazon.com/cli/). Make sure you have an AWS user that has S3 access, then run:

```bash
$ aws configure
```

Add the two environment variables to your computer:

- `SLACK_URL`
- `PINBOARD_TOKEN`

Then, add a cron job that somehow runs `remind.py`:

```crontab
0 * * * * python3 /home/james/linkreminder/.execute.py
```

I created an `.execute.sh` file in the root of this project (don't worry, it's gitignore'd) that sets the right environment variables, runs the [pyenv](https://github.com/pyenv/pyenv) setup stuff, and then runs `remind.py`.

```bash
#!/bin/bash

export PATH=~/.pyenv/shims:~/.pyenv/bin:"$PATH"
TZ='America/Los_Angeles'; export TZ
export SLACK_URL=https://hooks.slack.com/services/<nope>
export PINBOARD_TOKEN=<nope>

python /home/james/linkreminder/remind.py > /home/james/linkreminder/.output.log 2>&1
```
