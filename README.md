# MonitorR

A plug-in that regularly obtains the location of online players for recording, and sets a restricted area at the same time. If the player is detected in the restricted area, it will be broadcast in the server and recorded.  

The functional idea of this plug-in comes from [Monitor](https://github.com/W-Kazdel/Monitor), but because the latter has some functional bugs and does not have a very user-friendly experience, we reworked it.  

The plug-in will recognize the bot, and `will not` record and judge the location of the bot.  

[中文](README_cn.md) | English  

## Usage

Using !!mr or !!mr help to get help messages.  

![image](pics/help.png)  

The details of each parameter can be viewed by moving the mouse over the text in the game!  

At present, the text inside the plugin does not provide English version. Be aware that if there is a strong demand, please inform the issue and I will consider providing it.  

## Install

Download the plug-in `monitor.py` file to the `plugins` directory of MCDR. Note that the plug-in needs to be supported by MCDRv1.3 and above.

The plug-in depends on MinecraftDataAPI, see [MinecraftDataAPI](https://github.com/MCDReforged/MinecraftDataAPI/blob/master/README_cn.md).  

It is recommended to use the `ujson` third-party json library, whose IO efficiency is much higher than the default `json` library. But even if it is not installed, the plugin will use the `json` standard library by default.  

## Configuration

Enabling the plugin for the first time will generate a default configuration folder and configuration file in the `config` directory of MCDR.  

The path of the configuration file is `config/monitor_reforged/config.json`, and its content is:  

```
{
    "interval": 15,
    "permissions": {
        "add": 3,
        "del": 3,
        "list": 1,
        "range": 3,
        "reload": 3
    },
    "point": {
        "radius": 200,
        "contain_y": false,
    },
    "range": {
        "contain_y": false,
    }
}
```

Among them, `interval` represents the minimum time period for repeatedly obtaining all player positions, in seconds. `interval` is not a strictly accurate time period. This is because obtaining the player's position information multiple times in a small time will cause lag. Therefore, every time you start acquiring all player information, you will actively wait for 200 ms when you acquire a player's information. Finally count all the waiting time, let the minimum time minus total waiting time, then actively wait for the result time, and start the next cycle of acquiring all players. There are two reasons why the time is not strict here. The first is that the calculation of the waiting time is simply adding up all the sleep time, but doesn't include the time of IO operation or player information obtaining; the second is if there are a lot of players, the actual time period will inevitably exceed the time period specified in the configuration file. For example, when the number of online players on the server exceeds 75, the total waiting time for obtaining each player's information each time exceeds the default 15 seconds. At this time, if the setting is still maintained for 15 seconds, the program will ignore this 15 seconds and strictly rely on the accumulation of waiting time to obtain each player's information. The final manifestation is that there is no delay between the loops of obtaining all player information, but only the 200 ms delay of obtaining two different players next to each other.   

The `permissions` item has many sub-items, which respectively indicate the MCDR permission level required for each command. For details, see [MCDR Permission](https://mcdreforged.readthedocs.io/en/latest/permission.html)  

The sub-items of the `point` item indicate the configuration of the protection point. Among them, `radius` indicates the default protection point radius. Note that the configuration item here only indicates the default value of the radius that should be used if the `radius` parameter is not specified when generating the protection point. In fact, when you use the default value to generate a protection point, After changing this default value, the value of this protection point will `not` be modified with your modification, but still keep the previous default value. `contain_y` also indicates whether to calculate the y coordinate by default, the same as `radius`, modifying the default value after generating the protection point `will not` cause the previous default value to be modified.  

The sub-items of the `range` item indicate the configuration of the protected area. Among them, `contain_y` indicates whether to calculate the y coordinate by default, which is the same as the `radius` of the `point` item. Modifying the default value after generating the protected area will not cause the previous default value to be modified.  

If you need to modify the information of the created coordinate point/area, you can refer to the next section `Generate File` and directly modify the `site.json` file. However, it is more recommended to delete the protection point/zone and recreate it.  

## Generate File

After running the plug-in for the first time, the plug-in will generate its own plug-in directory in the `config` directory of MCDR with the name `monitor_reforged`. This directory contains files `config.json`, `site.json` and `log` folders.  

See the previous section for the content of `config.json`.  

The information of all protected points/zones is stored in `site.json`. The file is parsed according to an example below:  

```
[
    {
        "type": "point",
        "name": "test",
        "x": 100,
        "y": 60,
        "z": 100,
        "world": "minecraft:overworld",
        "radius": 200,
        "contain_y": false
    },
    {
        "type": "range",
        "name": "test2",
        "x1": 100,
        "y1": 60,
        "z1": 100,
        "x2": 200,
        "y2": 60,
        "z2": 200,
        "world": "minecraft:overworld",
        "contain_y": false
    }
]

```

As you can see, this json text is actually a list of dicts.  

Each dict has a `type` item, which has two values: `point` and `range`. Used to distinguish whether it is a protected point or a protected area.  

Each protection point/area contains the `name` attribute, which is used as a unique identifier.  

Each protection point/area contains the `world` attribute, which represents the world dimension in which the protection point/area is located.  

Each protection point/area contains the attribute `contain_y`, which indicates whether the protection point/area calculates the y coordinate.  

Since the protection point is a point, it only needs to store the 3D coordinate triples of `x`, `y` and `z`.  

The unique `radius` of the protection point indicates the radius of the warning zone.  

The protected area is a rectangle(cuboid), so it can be represented by two corner points. So two 3D coordinate triples of `x`, `y` and `z` are stored. It should be noted that the two 3D coordinates stored in the file are not necessarily equal to the parameters entered before. Because there can be multiple pairs of corner points forming the same rectangle(cuboid), the record will only record a pair of corner points on the main diagonal. Intuitively, the first 3D coordinate are all mininum values, another 3D coordinate are all maximum values. At the code level, this can simplify  the logic and make the judgment process running faster and simpler. If you need to modify this part, please make sure that the result of your modification still complies with the above rules. Otherwise it will cause logic errors.  

The `log` folder is responsible for saving the players' coordinate records, which are saved in the `log.json` file for subsequent review (or some other purposes, such as convicting genius). At the same time, it will also record the alarm when the player is near a protection point/area. Every time the plugin is loaded (like starting MCDR and reloading the plug-in etc.), the currently record file will be renamed according to the time to prevent a file from being too large. It should be noted here that although each record file is a json file, the text inside is not strictly json text. In fact, the text inside is divided by line breaks, and each line is a json text. If you need to parse, please pay attention.  