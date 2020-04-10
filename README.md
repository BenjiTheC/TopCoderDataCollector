# Top Coder Data Collector

The data scraper for Benjamin's SSW 900 thesis.

## Notes on the process of data

> I believe it's important to document how the data is obtained and processed before it's uploaded into the database. The section describes how the data is obtained and how some edge cases are handle.

- All past challenges data are fetched from the endpoint `http://api.topcoder.com/v4/challenges?filter=status%3DCOMPLETED&limit=50&offset={offset}` where `offset` is dynamically set to fetch the challenges. The largetest possible number of challenges to fetch in one request (i.e param `limit`) is _50_.

   Note that the although the challenges are filtered by the _COMPLETED_ status, **there are challenges with NO registrant nor winner**. Indicates that these may be the _starved challenges_. This endpoint is how the TopCoder website obtains the "past challenges" data.

- During processing the challenge data, the missing values are handled as below:

  - If the data field is a string type, missing value will be filled with empty string `''`.
  - If the data field is a number type, missing value will be fileed with negative one `-1`.
  - If the data field is a datatime type, missing value will be filed with `None` in Python, standing for `null`.
  - There are winners with no submission time or rank or points, it's handled as the same described above.

  The reason why the missing datetime is filled with `None` is that the setting of MySQL doesn't allowed "zero" datetime. And I don't have access to change the setting.

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
