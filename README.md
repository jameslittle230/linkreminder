I listened to a talk by [Andy Matuschak](https://andymatuschak.org/) recently. He talked about a lot of things relating to his research around transformative tools for thought, but one thing that stuck in my brain was this sort of demo he gave. In this demo, he would write down a question, and then he would get reminded of that question with exponential backoff: the question would reappear in a few days, then again after a few more, then again after a few weeks, months, etc. This framework allowed him to revisit ideas in his daily writing and build up different reactions to the same question over time, which could then be compiled into a larger, more comprehensive artifact that answered that original question.

Here, I've made a script that you run every hour via a cron job. This script will find Pinboard articles you've saved and remind you of them, with exponential backoff, letting you explore the links you've saved and maybe have reactions to them over the course of years.

## Setup

Add the two environment variables to your computer:

- `SLACK_URL`
- `PINBOARD_TOKEN`

Then, add a cron job that runs `remind.py`:

```
5 * * * * python3 remind.py
```

(This will actually run at five minutes past every hour.)