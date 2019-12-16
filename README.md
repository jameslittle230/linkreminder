- Remind me about Pinboard links with an exponential backoff
- Get four Slack messages per day with links to saved articles
- I want to get reminded about a given article with some frequency at the beginning, then with runoff at the end.
- I will have to make sure the frequency in the beginning is not too frequent, to ensure that more links have the ability to be "in the running."
- New links get "in the running" within n days; old links get "in the running" randomly but with no urgency.
- Data model can just be "don't notify before" date, and the database can be pre-filled with existing articles

Reminder frequency:
- Four days
- Eight days
- 18 days
- 45 days
- 90 days
- 180 days
- 365 days

I'm not sure what'll happen after that?

## Environment Variables

- `SLACK_URL`
- `PINBOARD_TOKEN`