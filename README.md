## Url Notifier
Alfred Workflow + Server provider + iOS Client to open links from Mac on iOS device in 1 action

## User guide
Setup is easy:
1. Download iOS application
2. Install Alfred workflow
3. Launch iOS app
4. Allow push notifications
5. Wait few seconds for device id showing up
6. In alfred type ```[pu add {device id from iOS app} {device name}]```

Now you can send links with ```[pu yandex.ru]```
You can add as many devices as you wish. Choose device to push in Alfred's list or push to all of them simultaneously.
To remove device just type ```[pu rm {device name or id}]```


## Developer guide
You can create your own desktop clients.
There are some methods for you here:

```
/url/, POST
```
#### Parameters:
url – url to open on the devices
udids – an array with destination devices's id

#### Example:
```
data = {
    "url":"yandex.ru",
    "udids":["SIH3e", "KKeU8w"]
}
```
