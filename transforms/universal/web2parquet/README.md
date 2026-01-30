# Web Crawler to Parquet

This transform crawls the web and downloads files in real-time.

This first release of the transform, only accepts the following 4 parameters. Additional releases will extend the functionality to allow the user to specify additional constraints such as mime-type, domain-focus, etc.


## Parameters

For configuring the crawl, users need to specify the following parameters:

| parameter:type | Description |
| --- | --- |
| urls:list | list of seed URLs (i.e., ['https://thealliance.ai'] or ['https://www.apache.org/projects','https://www.apache.org/foundation']). The list can include any number of valid URLS that are not configured to block web crawlers |
|depth:int | control crawling depth |
| downloads:int | number of downloads that are stored to the download folder. Since the crawler operations happen asynchronously, the process can result in any 10 of the visited URLs being retrieved (i.e. consecutive runs can result in different files being downloaded) |
| folder:str | folder where downloaded files are stored. If the folder is not empty, new files are  added or replace the existing ones with the same URLs |


## Install the transform

The transform can be installed directly from pypi and has a dependency on the data-prep-toolkit and the data-prep-connector

Set up the local environment to run Jupyter notebook:
```
python -v venv venv
source venv/bin/activate
pip install uv
uv pip install jupyter lab
```
Install pre-requisites:

```
uv pip install data-prep-connector
uv pip install data-prep-toolkit>=0.2.2.dev2
uv pip install 'data-prep-toolkit-transforms[web2parquet]>=0.2.2.dev3'
```

If working from a fork in the git repo, from the root folder of the git repo, do the following:

```
cd transforms/universal/web2parquet
make venv
source venv/bin/activate
uv pip install -r requirements.txt
```

## Invoking the transform from a notebook

In order to invoke the transfrom from a notebook, users must enable nested asynchronous ( https://pypi.org/project/nest-asyncio/ ), import the transform class and call the `transform()`function as shown in the example below:


```
import nest_asyncio
nest_asyncio.apply()
from dpk_web2parquet.transform import Web2Parquet
Web2Parquet(urls= ['https://thealliance.ai/'],
                    depth=2, 
                    downloads=10,
                    folder='downloads').transform()
````
