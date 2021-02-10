# Top Coder Data Collector

The data scraper for collecting research data from Topcoder.com

## Dependency

**This repo is written in Python 3.9.1.**

run

```sh
python3 -m pip install -r requirements.txt
```

to install the packages needed in the code. A virtural environment is recommended.

## Command Line Interface design

### Fetcher

> Fetch the data from Topcoder.com

```sh
python3 topcoder_data_collecter.py --with-registrant --since 2014-1-1 --to 2020-12-31 --proxy 1080
```

### Uploader

To initiate and write data into the MongoDB database, make sure that the data JSON files are placed in the `data` folder under the repository's root. And run following command.

```sh
python3 topcoder_data_uploader.py --debug # You can emit debug flag, it will print less information
```

> SQL database's writing method is under development

## Major APIs and the documentation

Currently Topcoder publish a new version of API - v5. [Here is the official anouncement](https://www.topcoder.com/an-update-from-the-product-development-team-challenge-v5-api-release/).

> **NOTE**: The dev version of api is exposed via <https://api.topcoder-dev.com/v5/{endpoint}>, especially for resource api there are changes deployed in dev version but not in production version. The code is using _entirely_ production version of api for the purpose of stability.

1. Challenge data service:
   * GitHub repo: <https://github.com/topcoder-platform/challenge-api>
   * Swagger UI doc: <http://api.topcoder.com/v5/challenges/docs/>
   **Important**: The url <https://api.topcoder.com/v5/challenges/> has two pagination parameters `perPage` and `page`, where `perPage` stands for the number of data objects (challenges) per fetch and `page` is number of pages to fetch. `perPage` has an official value interval of `[1, 100]`, whereas `page` has no specified limit. _HOWEVER, if the product of `perPage` and `page` is **greater than 10,000**, there will be only empty array returned._

   > The registrants' data of a challenge is missing from v5 API, need to use v4 api to fetch registrant data
   >
   > ```sh
   > http://api.topcoder.com/v4/challenges/{legacyID}
   > ```

2. Challenge Resource data service:
   * GitHub repo: <https://github.com/topcoder-platform/resources-api>
   * Swagger UI doc: <http://api.topcoder.com/v5/resources/docs/>
   This endpoint is for fetching the resource list for a challenge, see [this GitHub issue](https://github.com/topcoder-platform/challenge-api/issues/367) for detail.

3. Project data service (_only accessible for authenticated user_):
   * GitHub repo: <https://github.com/topcoder-platform/tc-project-service>
   * Swagger UI doc: <http://api.topcoder.com/v5/projects/docs/>

4. Member data service:
   * GitHub repo: <https://github.com/topcoder-platform/member-api>
   * Swagger UI doc: It's not available from any url but there is a yaml doc file in the repository: <https://github.com/topcoder-platform/member-api/blob/develop/docs/swagger.yaml>
