# sm2
Syncthing Multi Server Monitor



## The goal:
Monitor multiple syncthing instances while using as little diskspace(docker image size) & memory while doing it.

This affected the following parts:
- no use of an already made syncthing library (this also allows sm2 to only ever call GET endpoinds)
- no fancy ui -> lower diskspace, loadtime ( I also could not make a fancy ui if I tried)
- no logging exept printing to console logging increased the ram usage by ~50%


This project was made with very little sleep so there will be typo's, missed conventions, ... let me know if you see anything.
Any feedback is appreciated.

usage:
add your syncthing devices via a json file or env variables:

json:
``` [
    {"name" : "device1", 
    "url": "10.0.0.1:8384",
    "api_key": "API_KEY" },
    {"name" : "device2", 
    "url": "10.0.0.2:8384",
    "api_key": "API_KEY" }
    ]
```
env variables:
```
      - DEV_NAME_1=device1
      - DEV_URL_1=10.0.0.1:8384
      - DEV_API_KEY_1=API_KEY
      - DEV_NAME_2=device2
      - DEV_URL_2=10.0.0.2:8384
      - DEV_API_KEY_2=API_KEY
```      

The default protocol used is http if you require https for a device you'll need to add it to the url


# docker-compose example
```
  sm2:
    image: nwarelab/sm2:latest
    container_name: sm2
    restart: always
    environment:
      - DEV_NAME_1=device1
      - DEV_URL_1=10.0.0.1:8384
      - DEV_API_KEY_1=API_KEY
      - DEV_NAME_2=device2
      - DEV_URL_2=10.0.0.2:8384
      - DEV_API_KEY_2=API_KEY
    ports:
      - 8456:8456
```

# TODO's
Handle non server devices that are not online 24/7
gotify for notifications ?
figure out healthcheck that has less cpu impact