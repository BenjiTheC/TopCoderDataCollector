# Top Coder Data Collector

The data scraper for collecting research data from Topcoder.com

## Command Line Interface design

```sh
python3 topcoder_data_collecter.py --with-registrant --since 2014-1-1 --to 2020-12-31 --proxy 1080
```

## Major APIs and the documentation

Currently Topcoder publish a new version of API - v5. [Here is the official anouncement](https://www.topcoder.com/an-update-from-the-product-development-team-challenge-v5-api-release/).

1. Challenge data service:
   * GitHub repo: <https://github.com/topcoder-platform/challenge-api>
   * Swagger OpenAPI doc: <http://api.topcoder.com/v5/challenges/docs/>
   **Important**: The url <https://api.topcoder.com/v5/challenges/> has two pagination parameters `perPage` and `page`, where `perPage` stands for the number of data objects (challenges) per fetch and `page` is number of pages to fetch. `perPage` has an official value interval of `[1, 100]`, whereas `page` has no specified limit. _HOWEVER, if the `page` value is **greater than 100**, there will be only empty array returned._

   > The registrants' data of a challenge is missing from v5 API, need to use v4 api to fetch registrant data
   >
   > ```sh
   > http://api.topcoder.com/v4/challenges/{legacyID}
   > ```

2. Project data service (_only accessible for authenticated user_):
   * GitHub repo: <https://github.com/topcoder-platform/tc-project-service>
   * Swagger OpenAPI doc: <http://api.topcoder.com/v5/projects/docs/>

3. Member data service:
   * GitHub repo: <https://github.com/topcoder-platform/member-api>
   * Swagger OpenAPI doc: It's not available from any url but there is a yaml doc file in the repository: <https://github.com/topcoder-platform/member-api/blob/develop/docs/swagger.yaml>
