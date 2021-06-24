#!/usr/bin/env python
# -*- codeing:utf-8 -*-

from datetime import datetime
import os
import logging
import math
import time
from typing import List, Any, Tuple, Union

# ujson比json快 所以我就是要用ujson
try:
    import ujson
except ImportError:
    import json as ujson

from mcdreforged.minecraft.rtext import RAction, RTextList, RText
from mcdreforged.api.decorator import new_thread
from mcdreforged.plugin.server_interface import ServerInterface
from mcdreforged.info import Info

PLUGIN_METADATA = {
    'id': 'monitor_reforged',
    'version': '1.0.0',
    'name': 'MonitorR',
    'description': 'Adapted from Monitor, a more complete monitoring plug-in.',
    'author': 'XiaoHuiHui',
    'link': 'https://github.com/XiaoHuiHui233/MonitorR',
    'dependencies': {
        'minecraft_data_api': '>=1.1.0',
    }
}

DEFAULT_CONFIG = {
    'interval': 15,
    'permissions': {
        'add': 3,
        'del': 3,
        'list': 1,
        'range': 3,
        'reload': 3
    },
    'point': {
        'radius': 200,
        'contain_y': False,
    },
    'range': {
        'contain_y': False,
    }
}

# hard code
DIMENSIONS = {
    '0': 'minecraft:overworld',
    '-1': 'minecraft:the_nether',
    '1': 'minecraft:the_end',
    'overworld': 'minecraft:overworld',
    'the_nether': 'minecraft:the_nether',
    'the_end': 'minecraft:the_end',
    'nether': 'minecraft:the_nether',
    'end': 'minecraft:the_end',
    'minecraft:overworld': 'minecraft:overworld',
    'minecraft:the_nether': 'minecraft:the_nether',
    'minecraft:the_end': 'minecraft:the_end'
}


HELP_MSG = [
    RText('----------- §aMCDR 监控插件帮助信息 §f-----------'),
    RTextList(
        RText('§b!!mr add '),
        RText('§f<§aname§f> ').set_hover_text(
            RText(
                '§aname§f参数表示保护点的唯一标识符\n'
                '参数类型为§e字符串§f，必填\n'
                '注意:\n'
                '  此参数不能输入§dhere§f和能被解析为§e§l数字§r的§e字符串§f\n'
                '  这会导致可能的§c解析错误§f并报错'
            )
        ),
        RText('<§ax§f> ').set_hover_text(
            RText(
                '§ax§f参数表示保护点的x坐标\n'
                '参数类型为§e数字§f，必填\n'
                '注意:\n'
                '  此参数会被强制转化为§e§l整数§r，即使输入是§e浮点数§f\n'
                '  若§c无法解析输入§f(通常是输入中带有§c§l非法字符§r)会报错'
            )
        ),
        RText('<§ay§f> ').set_hover_text(
            RText(
                '§ay§f参数表示保护点的y坐标\n'
                '参数类型为§e数字§f，必填\n'
                '注意:\n'
                '  此参数会被强制转化为§e§l整数§r，即使输入是§e浮点数§f\n'
                '  若§c无法解析输入§f(通常是输入中带有§c§l非法字符§r)会报错'
            )
        ),
        RText('<§az§f> ').set_hover_text(
            RText(
                '§az§f参数表示保护点的z坐标\n'
                '参数类型为§e数字§f，必填\n'
                '注意:\n'
                '  此参数会被强制转化为§e§l整数§r，即使输入是§e浮点数§f\n'
                '  若§c无法解析输入§f(通常是输入中带有§c§l非法字符§r)会报错'
            )
        ),
        RText('[§aworld§f] ').set_hover_text(
            RText(
                '§aworld§f参数表示保护点所处的世界名称\n'
                '参数类型为§e数字§f或§e字符串§f，选填\n'
                '参数默认为§d主世界§f，但可以在配置里更改默认\n'
                '支持的输入有:\n'
                '  §d0§f、§d-1§f、§d1§f、§doverworld§f、§dthe_nether§f、§dthe_end§f、§dnether§f、\n'
                '  §dend§f、§dminecraft:overworld§f、§dminecraft:the_nether§f、\n'
                '  §dminecraft:the_end§f\n'
                '  若不属于§c上述范围§f的输入会报错'
            )
        ),
        RText('[§aradius§f] ').set_hover_text(
            RText(
                '§aradius§f参数表示保护点周围的保护半径\n'
                '这表示保护范围是一个向上取整后的圆\n'
                '参数类型为§e数字§f，选填\n'
                '参数默认为§d200§f，表示半径§d200格§f的区域\n'
                '可以在配置里更改默认\n'
                '注意:\n'
                '  此参数接受任何§e浮点数§f\n'
                '  但是进行距离计算的输入坐标仍然是§e整数§f坐标\n'
                '  距离计算的结果存在开平方，因此可能是§e浮点数§f\n'
                '  若§c无法解析输入§f(通常是输入中带有§c§l非法字符§r)会报错'
            )
        ),
        RText('[§acontain_y§f]').set_hover_text(
            RText(
                '§acontain_y§f参数表示是否计算y轴\n'
                '若为是，则保护区实为§d球体§f，否则为§d圆柱§f\n'
                '参数类型为§e不区分大小写的§l布尔表达式§r§f，选填\n'
                '参数默认为§dFalse§f，即不参与计算\n'
                '注意:\n'
                '  支持的输入仅有不区分大小写的§dtrue§f或者§dfalse§f\n'
                '  若不属于§c上述范围§f的输入会报错'
            )
        ),
    ),
    RText(' - §d添加一个保护的坐标点'),
    RTextList(
        RText('§b!!mr add '),
        RText('§f<§aname§f> ').set_hover_text(
            RText(
                '§aname§f参数表示保护点的唯一标识符\n'
                '参数类型为§e字符串§f，必填\n'
                '注意:\n'
                '  此参数不能输入§dhere§f和能被解析为§e§l数字§r的§e字符串§f\n'
                '  这会导致可能的§c解析错误§f并报错'
            )
        ),
        RText('§bhere '),
        RText('[§aworld§f] ').set_hover_text(
            RText(
                '§aworld§f参数表示保护点所处的世界名称\n'
                '即§d坐标§f仍然是§d玩家坐标§f，但可以设置到§d§l别的世界§r\n'
                '参数类型为§e数字§f或§e字符串§f，选填\n'
                '参数默认为§d玩家所在的世界§f\n'
                '支持的输入有:\n'
                '  §d0§f、§d-1§f、§d1§f、§doverworld§f、§dthe_nether§f、§dthe_end§f、§dnether§f、\n'
                '  §dend§f、§dminecraft:overworld§f、§dminecraft:the_nether§f、\n'
                '  §dminecraft:the_end§f\n'
                '  若不属于§c上述范围§f的输入会报错'
            )
        ),
        RText('[§aradius§f] ').set_hover_text(
            RText(
                '§aradius§f参数表示保护点周围的保护半径\n'
                '这表示保护范围是一个向上取整后的圆\n'
                '参数类型为§e数字§f，选填\n'
                '参数默认为§d200§f，表示半径§d200格§f的区域\n'
                '可以在配置里更改默认\n'
                '注意:\n'
                '  此参数接受任何§e浮点数§f\n'
                '  但是进行距离计算的输入坐标仍然是§e整数§f坐标\n'
                '  距离计算的结果存在开平方，因此可能是§e浮点数§f\n'
                '  若§c无法解析输入§f(通常是输入中带有§c§l非法字符§r)会报错'
            )
        ),
        RText('[§acontain_y§f]').set_hover_text(
            RText(
                '§acontain_y§f参数表示是否计算y轴\n'
                '若为是，则保护区实为§d球体§f，否则为§d圆柱§f\n'
                '参数类型为§e不区分大小写的§l布尔表达式§r§f，选填\n'
                '参数默认为§dFalse§f，即不参与计算\n'
                '注意:\n'
                '  支持的输入仅有不区分大小写的§dtrue§f或者§dfalse§f\n'
                '  若不属于§c上述范围§f的输入会报错'
            )
        ),
    ),
    RText(' - §d添加一个保护的坐标点在玩家所在的位置'),
    RTextList(
        RText('§b!!mr range '),
        RText('§f<§aname§f> ').set_hover_text(
            RText(
                '§aname§f参数表示保护区的唯一标识符\n'
                '参数类型为§e字符串§f，必填\n'
                '注意:\n'
                '  此参数不能输入§dhere§f和能被解析为§e§l数字§r的§e字符串§f\n'
                '  这会导致可能的§c解析错误§f并报错'
            )
        ),
        RText('<§apoint1§f> ').set_hover_text(
            RText(
                '§apoint1§f参数表示保护区的角点1\n'
                '参数类型为§e字符串§f或§e§l数字三元组§r，必填\n'
                '此参数可接受的输入为:\n'
                '  §dhere§f、§d已存在的§l保护点§r§d的名称§f\n'
                '  以及§d(x, y, z)坐标§f\n'
                '  关于坐标的输入要求等同于§badd§f子命令\n'
                '注意:\n'
                '  若使用§d已存在的§l保护点§r§d的名称§f作为参数\n'
                '  则必须保证两角点处于§d同一世界§f'
            )
        ),
        RText('<§apoint2§f> ').set_hover_text(
            RText(
                '§apoint2§f参数表示保护区的角点2\n'
                '参数类型为§e字符串§f或§e§l数字三元组§r，必填\n'
                '此参数可接受的输入为:\n'
                '  §dhere§f、§d已存在的§l保护点§r§d的名称§f\n'
                '  以及§d(x, y, z)坐标§f\n'
                '  关于坐标的输入要求等同于§badd§f子命令\n'
                '注意:\n'
                '  若使用§d已存在的§l保护点§r§d的名称§f作为参数\n'
                '  则必须保证两角点处于§d同一世界§f'
            )
        ),
        RText('[§aworld§f] ').set_hover_text(
            RText(
                '§aworld§f参数表示保护区所处的世界名称\n'
                '参数类型为§e数字§f或§e字符串§f，选填\n'
                '参数默认会针对两个§e角点§f的输入进行所处§e世界§f的推断\n'
                '但注意，若存在歧义，则§c§l直接报错§r，并不会被本参数覆盖\n'
                '支持的输入有:\n'
                '  §d0§f、§d-1§f、§d1§f、§doverworld§f、§dthe_nether§f、§dthe_end§f、§dnether§f、\n'
                '  §dend§f、§dminecraft:overworld§f、§dminecraft:the_nether§f、\n'
                '  §dminecraft:the_end§f\n'
                '  若不属于§c上述范围§f的输入会报错'
            )
        ),
        RText('[§acontain_y§f]').set_hover_text(
            RText(
                '§acontain_y§f参数表示是否计算y轴\n'
                '若为是，则保护区会计算角点的§dy坐标§f差值\n'
                '否则会考虑§d0§f到§d255§f的全部高度\n'
                '参数类型为§e不区分大小写的§l布尔表达式§r§f，选填\n'
                '参数默认为§dFalse§f，即不参与计算\n'
                '注意:\n'
                '  支持的输入仅有不区分大小写的§dtrue§f或者§dfalse§f\n'
                '  若不属于§c上述范围§f的输入会报错'
            )
        ),
    ),
    RText(' - §d添加一个两点围成的矩形（长方体）作为保护区'),
    RTextList(
        RText('§b!!mr del '),
        RText('§f<§aname§f> ').set_hover_text(
            RText(
                '§aname§f参数表示保护点/区的唯一标识符\n'
                '参数类型为§e字符串§f，必填\n'
                '若输入不存在的唯一标识符则报错并返回'
            )
        ),
        RText(' - §d删除一个保护的坐标点/区')
    ),
    RTextList(
        RText('§b!!mr list §f - §d显示所有已有保护的坐标点/区'),
        RText('§f §l[§a§l√§f§l]§r').set_hover_text(
            RText('§e点我执行此命令')
        ).set_click_event(
            RAction.run_command,
            '!!mr list'
        )
    ),
    RTextList(
        RText('§b!!mr reload§f - §d重载插件'),
        RText('§f §l[§a§l√§f§l]§r').set_hover_text(
            RText('§e点我执行此命令')
        ).set_click_event(
            RAction.run_command,
            '!!mr reload'
        )
    ),
    RText('----------------------------------------------'),
]

config_folder = f"./config/{PLUGIN_METADATA['id']}"
log_folder = f'{config_folder}/logs'
log_file = f'{log_folder}/log.json'
site_file = f'{config_folder}/site.json'
config_file = f'{config_folder}/config.json'

bots = set()
players = set()
monitor = None
record_fp = None
sites = {}
config = DEFAULT_CONFIG
logger = logging.getLogger("MonitorR")
running = False


class ParseError(Exception):
    """一个表示命令解析失败的异常.
    """
    pass


def check_config() -> None:
    for key in DEFAULT_CONFIG:
        if key not in config:
            logger.warn(f'Config配置项缺失：{key}，已默认补全。')
            config[key] = DEFAULT_CONFIG[key]
        elif isinstance(DEFAULT_CONFIG[key], dict):
            for key1 in DEFAULT_CONFIG[key]:
                if key1 not in config[key]:
                    logger.warn(f'Config配置项缺失：{key}.{key1}，已默认补全。')
                    config[key][key1] = DEFAULT_CONFIG[key][key1]


def save_config() -> None:
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
    with open(config_file, 'w', encoding='utf-8') as wf:
        ujson.dump(
            config,
            wf,
            ensure_ascii=False,
            indent=4
        )

def load_config() -> None:
    global config
    if not os.path.exists(config_file):
        logger.warn('Config文件不存在！自动生成覆盖！')
        save_config()
        return
    try:
        with open(config_file, 'r', encoding='utf-8') as rf:
            config = ujson.load(rf)
    except:
        logger.warn('Config文件格式错误！自动生成覆盖！')
        save_config()
    check_config()


def split_log() -> None:
    global record_fp
    if os.path.exists(log_file):
        time = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        os.rename(log_file, f'./records/{time}.json')
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    record_fp = open(log_file, 'w+', encoding='utf-8')


def save_sites() -> None:
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
    with open(site_file, 'w', encoding='utf-8') as wf:
        ujson.dump(
            sites,
            wf,
            ensure_ascii=False,
            indent=4
        )


def load_sites() -> None:
    global sites
    if not os.path.exists(site_file):
        logger.warn('Sites文件不存在！自动生成覆盖！')
        save_sites()
        return
    try:
        with open(site_file, 'r', encoding='utf-8') as rf:
            sites = ujson.load(rf)
    except:
        logger.warn('Sites文件格式错误！自动生成覆盖！')
        save_sites()


def on_help(server: ServerInterface, info: Info) -> None:
    for rtext in HELP_MSG:
        server.reply(info, rtext)  


def permission_check(server: ServerInterface, info: Info, subcmd: str) -> bool:
    if info.is_player:
        if server.get_permission_level(info) < config['permissions'][subcmd]:
            server.reply(info, RText(f'§f[§aMonitorR§f][§cWARN§f] §c你没有足够的权限执行此命令！'))
            return False
    return True


def on_reload(server: ServerInterface, info: Info, args: List[str]) -> None:
    if not permission_check(server, info, 'reload'):
        return
    try:
        load_config()
        load_sites()
        server.reply(info, RText(f'§f[§aMonitorR§f][§2INFO§f] §2重载成功！'))
    except Exception as err:
        server.reply(info, RText(f'§f[§aMonitorR§f][§cERROR§f] §c发生错误！').set_hover_text(f'{repr(err)}'))
        raise err


def name_check(name: str) -> None:
    if name in sites:
        raise ParseError(f'已有名称为{name}的保护点/区，拒绝添加！')
    if name == 'here':
        raise ParseError(f'here是命令解析中的关键字，不能被设为名称！')
    else:
        try:
            int(name)
        except:
            pass
        else:
            raise ParseError(f'名称不能是纯数字，这会导致解析出现二义性！')


def here_to_pos(server: ServerInterface, info: Info) -> Union[Tuple[int, int, int, str], None]:
    if not info.is_player:
        server.reply(info, RText(f'§f[§aMonitorR§f][§cWARN§f] §e非玩家不能使用§bhere§e作为参数。'))
        return None
    try:
        data_api = server.get_plugin_instance('minecraft_data_api')
        if data_api is None:
            raise ImportError("找不到MinecraftDataAPI！")
    except:
        logger.error('获取DataAPI时发生错误！')
        server.reply(info, RText(f'§f[§aMonitorR§f][§cERROR§f] §c前置插件加载失败！'))
        return None
    else:
        pos = data_api.get_player_coordinate(info.player)
        dim = data_api.get_player_dimension(info.player)
        return (int(pos[0]), int(pos[1]), int(pos[2]), DIMENSIONS[str(dim)])


def on_add(server: ServerInterface, info: Info, args: List[str]) -> None:
    if not permission_check(server, info, 'add'):
        return
    try:
        name = args[0]
        if name in sites:
            raise ParseError(f'已有名称为{name}的保护点/区，拒绝添加！')
        if name == 'here':
            raise ParseError(f'here是命令解析中的关键字，不能被设为名称！')
        else:
            try:
                int(name)
            except:
                pass
            else:
                raise ParseError(f'名称不能是纯数字，这会导致解析出现二义性！')
        if args[1] == 'here':
            pos = here_to_pos(server, info)
            if pos is None:
                return
            x, y, z, world = pos
            idx = 2
        else:
            x = int(float(args[1]))
            y = int(float(args[2]))
            z = int(float(args[3]))
            idx = 4
            world = 'minecraft:overworld'
        if len(args) > idx:
            world = DIMENSIONS[args[idx]]
            idx += 1
        radius = config['point']['radius']
        if len(args) > idx:
            radius = float(args[idx])
            idx += 1
        contain_y = config['point']['contain_y']
        if len(args) > idx:
            if args[idx].lower() == 'true':
                contain_y = True
            elif args[idx].lower() == 'false':
                contain_y = False
            else:
                raise ParseError(
                    f'不支持的逻辑输入！你输入了{args[idx]}，'
                    '但是仅支持输入不区分大小写的true和false。'
                )
    except IndexError as err:
        raise ParseError(f'参数数量错误！详情：{repr(err)}')
    except ValueError as err:
        raise ParseError(f'无法解析的数值！详情：{repr(err)}')
    except KeyError as err:
        raise ParseError(f'不支持的世界类型输入！详情：{repr(err)}')
    else:
        sites[name] = {
            'type': 'point',
            'name': name,
            'x': x,
            'y': y,
            'z': z,
            'world': world,
            'radius': radius,
            'contain_y': contain_y
        }
        try:
            save_sites()
        except Exception as err:
            raise ParseError(f'保存文件时发生错误，详情：{repr(err)}')
        server.reply(info, RText(f'§f[§aMonitorR§f][§2INFO§f] §2执行成功！'))


def on_del(server: ServerInterface, info: Info, args: List[str]) -> None:
    if not permission_check(server, info, 'del'):
        return
    try:
        name = args[0]
        sites.pop(name)
    except IndexError as err:
        raise ParseError(f'参数数量错误！详情：{repr(err)}')
    except KeyError as err:
        raise ParseError(f'没有名称为{name}的保护点/区。')
    else:
        try:
            save_sites()
        except Exception as err:
            raise ParseError(f'保存文件时发生错误，详情：{repr(err)}')
        server.reply(info, RText(f'§f[§aMonitorR§f][§2INFO§f] §2执行成功！'))


def point_to_pos(server: ServerInterface, info: Info, name: str) -> Union[Tuple[int, int, int, str], None]:
    if sites[name]['type'] != 'point':
        server.reply(info, RTextList(
            RText('§f[§aMonitorR§f][§cWARN§f] '),
            RText(
                f'§e使用名称作为点的输入时必须保证类型是§b保护点§e而不是§b保护区§e！'
            ).set_hover_text(
                f"您提供的输入名称为{name}，其类型为{sites[name]['type']}，而我们需要point"
            )
        ))
        return None
    return (sites[name]['x'], sites[name]['y'], sites[name]['z'], sites[name]['world'])


def on_range(server: ServerInterface, info: Info, args: List[str]) -> None:
    if not permission_check(server, info, 'range'):
        return
    try:
        name = args[0]
        name_check(name)
        if 'here' in args[1:]:
            pos = here_to_pos(server, info)
            if pos is None:
                return
            x_h, y_h, z_h, world_h = pos
        if args[1] == 'here':
            x1 = x_h
            y1 = y_h
            z1 = z_h
            world_1 = world_h
            idx = 2
        elif args[1] in sites:
            pos = point_to_pos(server, info, args[1])
            if pos is None:
                return
            x1, y1, z1, world_1 = pos
            idx = 2
        else:
            x1 = int(float(args[1]))
            y1 = int(float(args[2]))
            z1 = int(float(args[3]))
            world_1 = 'minecraft:overworld'
            idx = 4
        if args[idx] == 'here':
            x2 = x_h
            y2 = y_h
            z2 = z_h
            world_2 = world_h
            idx += 1
        elif args[idx] in sites:
            pos = point_to_pos(server, info, args[idx])
            if pos is None:
                return
            x2, y2, z2, world_2 = pos
            idx += 1
        else:
            x2 = int(float(args[idx]))
            idx += 1
            y2 = int(float(args[idx]))
            idx += 1
            z2 = int(float(args[idx]))
            idx += 1
            world_2 = 'minecraft:overworld'
        if world_1 != world_2:
            server.reply(info, RText(f'§e请保证构成区域的两角点处于同一世界！'))
            return
        world = world_1
        if len(args) > idx:
            world = DIMENSIONS[args[idx]]
            idx += 1
        contain_y = config['range']['contain_y']
        if len(args) > idx:
            if args[idx].lower() == 'true':
                contain_y = True
            elif args[idx].lower() == 'false':
                contain_y = False
            else:
                raise ParseError(
                    f'不支持的逻辑输入！你输入了{args[idx]}，'
                    '但是仅支持输入不区分大小写的true和false。'
                )
    except IndexError as err:
        raise ParseError(f'参数数量错误！详情：{repr(err)}')
    except ValueError as err:
        raise ParseError(f'无法解析的数值！详情：{repr(err)}')
    except KeyError as err:
        raise ParseError(f'不支持的世界类型输入！详情：{repr(err)}')
    else:
        sites[name] = {
            'type': 'range',
            'name': name,
            'x1': min(x1, x2),
            'y1': min(y1, y2),
            'z1': min(z1, z2),
            'x2': max(x1, x2),
            'y2': max(y1, y2),
            'z2': max(z1, z2),
            'world': world,
            'contain_y': contain_y
        }
        try:
            save_sites()
        except Exception as err:
            raise ParseError(f'保存文件时发生错误，详情：{repr(err)}')
        server.reply(info, RText(f'§f[§aMonitorR§f][§2INFO§f] §2执行成功！'))


def on_list(server: ServerInterface, info: Info, args: List[str]) -> None:
    if not permission_check(server, info, 'list'):
        return
    server.reply(info, RText('§f保护点/区的列表：'))
    for name in sites:
        txt = RTextList(RText('§f    - '))
        if sites[name]['type'] == 'point':
            txt.append(RText(f'§b{name}').set_hover_text(
                RText(
                    f"§e类型§f: §b{sites[name]['type']}\n"
                    f"§e中心点§f: (§b{sites[name]['x']}§f, §b{sites[name]['y']}§f, §b{sites[name]['z']}§f)\n"
                    f"§e世界§f： §b{sites[name]['world']}\n"
                    f"§e半径§f： §b{sites[name]['radius']}\n"
                    f"§e是否计算y轴§f: §b{'是' if sites[name]['contain_y'] else '否'}"
                )
            ))
        elif sites[name]['type'] == 'range':
            txt.append(RText(f'§b{name}').set_hover_text(
                RText(
                    f"§e类型§f: §b{sites[name]['type']}\n"
                    f"§e角点1§f: (§b{sites[name]['x1']}§f, §b{sites[name]['y1']}§f, §b{sites[name]['z1']}§f)\n"
                    f"§e角点2§f: (§b{sites[name]['x2']}§f, §b{sites[name]['y2']}§f, §b{sites[name]['z2']}§f)\n"
                    f"§e世界§f： §b{sites[name]['world']}\n"
                    f"§e是否计算y轴§f: §b{'是' if sites[name]['contain_y'] else '否'}"
                )
            ))
        else:
             txt.append(RText(f'§b{name}').set_hover_text(
                RText(
                    f"§e类型§f: §b{sites[name]['type']}\n"
                )
             ))
        txt.append(
            RText('§f §l[§c§lX§f§l]§r').set_hover_text(
                RText('§e点我删除此项')
            ).set_click_event(
                RAction.run_command,
                f'!!mr del {name}'
            ))
        server.reply(info, txt)


commands = {
    'help': on_help,
    'add': on_add,
    'del': on_del,
    'range': on_range,
    'list': on_list,
    'reload': on_reload
}


def check_pos(server: ServerInterface, player: str, x: int, y: int, z: int, dim: str) -> bool:
    for name in sites:
        if dim != sites[name]['world']:
            continue
        status = False
        if sites[name]['type'] == 'point':
            if sites[name]['contain_y']:
                delta_x = sites[name]['x'] - x
                delta_y = sites[name]['y'] - y
                delta_z = sites[name]['z'] - z
                dis_2 = delta_x * delta_x + delta_y * delta_y + delta_z * delta_z
                dis = math.sqrt(dis_2)
            else:
                delta_x = sites[name]['x'] - x
                delta_z = sites[name]['z'] - z
                dis_2 = delta_x * delta_x + delta_z * delta_z
                dis = math.sqrt(dis_2)
            status = sites[name]['radius'] >= dis
        elif sites[name]['type'] == 'range':
            if sites[name]['contain_y']:
                status = x >= sites[name]['x1'] and x <= sites[name]['x2'] \
                    and y >= sites[name]['y1'] and y <= sites[name]['y2'] \
                    and z >= sites[name]['z1'] and z <= sites[name]['z2']
            else:
                status = x >= sites[name]['x1'] and x <= sites[name]['x2'] \
                    and z >= sites[name]['z1'] and z <= sites[name]['z2']
        if status:
            server.say(RText(
                f'§f[§aMonitorR§f][§cWARN§f] §c§l危§r§f！§b{player}§f在§e{name}§f游荡！！！'
            ))
            record_fp.write(ujson.dumps({
                'type': 'warning',
                'timestamp': time.time(),
                'player': str(player),
                'danger_zone': name
            }) + '\n')

# 监控
@new_thread('MonitorR')
def monitor(server: ServerInterface) -> None:
    data_api = server.get_plugin_instance('minecraft_data_api')
    remain_time = 0.0
    while running:
        remain_time = 15.0 - remain_time
        if remain_time < 0.0:
            remain_time = 0.0
        time.sleep(remain_time)
        if not running:
            break
        remain_time = 0.0
        for player in players:
            try:
                pos = data_api.get_player_coordinate(player)
                x = int(pos[0])
                y = int(pos[1])
                z = int(pos[2])
                dim = data_api.get_player_dimension(player)
                dim = DIMENSIONS[str(dim)]
                record_fp.write(ujson.dumps({
                    'type': 'timer',
                    'timestamp': time.time(),
                    'player': str(player),
                    'x': x,
                    'y': y,
                    'z': z,
                    'world': dim
                }) + '\n')
                check_pos(server, player, x, y, z, dim)
            except:
                continue
            time.sleep(0.2)
            if not running:
                break
            remain_time += 0.2
        record_fp.flush()


def on_load(server: ServerInterface, old: Any) -> None:
    server.register_help_message('!!mr', '重置版监控插件')
    global bots, players, running
    if old is not None:
        bots = old.bots
        players = old.players
    load_config()
    load_sites()
    split_log()
    running = True
    monitor(server)


def on_unload(server: ServerInterface) -> None:
    global running
    running = False
    global record_fp
    if record_fp is not None:
        record_fp.close()
        record_fp = None


@new_thread("MonitorR")
def on_user_info(server: ServerInterface, info: Info) -> None:
    # 真的不是我不喜欢MCDR新的命令树解析
    # 把简单东西复杂化了啊.....
    # 而且做成js的异步延迟回调的格式, 这种代码风格好难看啊!
    text = info.content
    if not text.startswith('!!mr'):
        return
    args = text.split(' ')
    if len(args) <= 1:
        on_help(server, info)
    else:
        subcmd = args[1]
        try:
            commands[subcmd](server, info, args[2:])
        except KeyError as err:
            server.reply(info, RText('§f[§aMonitorR§f][§cWARN§f] §c子命令错误！'))
            on_help(server, info)
        except ParseError as err:
            server.reply(info, RText('§f[§aMonitorR§f][§cWARN§f] §c参数错误！').set_hover_text(f'{err}'))


def on_player_joined(server: ServerInterface, player: str, info: Info) -> None:
    global bots, players
    if '[local] logged in with entity id' in info.content:
        bots.add(player)
    else:
        players.add(player)


def on_player_left(server: ServerInterface, player: str) -> None:
    global bots, players
    if player in bots:
        bots.remove(player)
    if player in players:
        players.remove(player)


def on_mcdr_stop(server: ServerInterface) -> None:
    on_unload(server)


def on_server_stop(server: ServerInterface, return_code: int) -> None:
    global bots, players
    bots = set()
    players = set()

