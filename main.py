from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Nodes
from astrbot.core.star.filter.event_message_type import EventMessageType
from .parser import BilibiliParser
import re

@register("astrbot_plugin_bilibili_bot_mod", "小鱼酱", "自动识别B站链接并转换为直链发送", "1.0.2")
class BilibiliBotPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.is_auto_parse = config.get("is_auto_parse", True)
        self.is_auto_pack = config.get("is_auto_pack", True)
        self.service_message = config.get("service_message", "B站bot为您服务 ٩( 'ω' )و")
        self.desc_template = config.get("desc_template", "标题：{title}\n作者：{author}\n简介：{desc}")
        max_video_size_mb = config.get("max_video_size_mb", 0.0)
        self.oversize_message = config.get("oversize_message", "当前视频大小为 {current_size} MB，超过限制的 {max_size} MB，已为您跳过发送。")
        self.parser = BilibiliParser(
            max_video_size_mb=max_video_size_mb,
            desc_template=self.desc_template,
            oversize_message=self.oversize_message,
        )

    async def terminate(self):
        pass

    @filter.event_message_type(EventMessageType.ALL)
    async def auto_parse(self, event: AstrMessageEvent):
        if not (self.is_auto_parse or bool(re.search(r'.?B站解析|b站解析|bilibili解析', event.message_str))):
            return
        result = await self.parser.build_nodes(event, self.is_auto_pack)
        if result is None:
            return
        nodes = result.get("nodes")
        oversize_tips = result.get("oversize_tips") or []
        # 先发送大小超限的提示
        for tip in oversize_tips:
            if tip:
                await event.send(event.plain_result(tip))
        if not nodes:
            return
        if self.service_message:
            await event.send(event.plain_result(self.service_message))
        if self.is_auto_pack:
            await event.send(event.chain_result([Nodes(nodes)]))
        else:
            for node in nodes:
                await event.send(event.chain_result([node]))
