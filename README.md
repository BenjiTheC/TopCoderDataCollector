# Top Coder Data Collector

The data scraper for Benjamin's SSW 900 thesis.

## API endpoints used to fetch the data 

> The API of TopCoder has gone through several iterations, and they mixed the different versions of endpoints in their producton environment. And the documentation of their API is a PAIN. After some time of trailing the error, here are the APIs I find that are still functional and serve meaningful data. 

- `http://api.topcoder.com/v4/challenges`

   The _v4_ version of challenge api is functional. There is a `filter` parameter provided which allows user to search the challenges with some variables. The detailed documentation can be found in [the GitHub repo of TopCoder](https://github.com/topcoder-platform/topcoder-api-challenges/blob/master/docs/DefaultApi.md#challengesGet).

   The problem is that this `filter` param seems not working with multiple conditions and only accepts a single key-value pair as param value. The past challenges listed in topcoder.com fetch the data using `http://api.topcoder.com/v4/challenges?filter=status=COMPLETED`.

- `http://api.topcoder.com/v4/challenges/{challenge_id}`

   This endpoint gets the detail of challenge by challenge id.

- `http://api.topcoder.com/v3/members/{handle}`

  - `http://api.topcoder.com/v3/members/{handle}/skills`

     This endpoint returns user's skills recognized in TopCoder

  - `http://api.topcoder.com/v3/members/{handle}/stats`

     This endpoint returns ranking and challenges records of user

   These _v3_ endpoints return detailed information of user. **The handle of user will be extracted only from the `winners` field of a challenge**.
