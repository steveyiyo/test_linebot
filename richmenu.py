# -*- coding: utf-8 -*-

import os
import sys

from dotenv import load_dotenv
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    RichMenuRequest,
    RichMenuArea,
    RichMenuSize,
    RichMenuBounds,
    URIAction,
    RichMenuSwitchAction,
    CreateRichMenuAliasRequest, PostbackAction
)

load_dotenv()

channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

configuration = Configuration(
    access_token=channel_access_token
)


def main():
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_blob_api = MessagingApiBlob(api_client)

        line_bot_api.delete_rich_menu_alias('richmenu-alias-a')

        # 2. Create rich menu A (richmenu-a)
        rich_menu_to_a_create = RichMenuRequest(
            size=RichMenuSize(width=2500,
                              height=1686),
            selected=True,
            name='richmenu-basic',
            chat_bar_text='查看更多資訊',
            areas=[
                RichMenuArea(
                    bounds=RichMenuBounds(
                        x=0,
                        y=0,
                        width=1250,
                        height=1686
                    ),
                    action=URIAction(
                        uri="https://liff.line.me/2001486622-g5oK1pGe"
                    )
                ),
                RichMenuArea(
                    bounds=RichMenuBounds(
                        x=1251,
                        y=0,
                        width=1250,
                        height=843
                    ),
                    action=PostbackAction(
                        label='會員卡',
                        displayText='顯示會員卡',
                        data='action=member_card'
                    )
                ),
                RichMenuArea(
                    bounds=RichMenuBounds(
                        x=1251,
                        y=844,
                        width=2500,
                        height=843
                    ),
                    action=URIAction(
                        uri="https://liff.line.me/2001486622-5ZB1OzmV"
                    )
                )
            ]
        )

        rich_menu_a_id = line_bot_api.create_rich_menu(
            rich_menu_request=rich_menu_to_a_create
        ).rich_menu_id

        # 3. Upload image to rich menu A
        with open('static/menu.png', 'rb') as image:
            line_bot_blob_api.set_rich_menu_image(
                rich_menu_id=rich_menu_a_id,
                body=bytearray(image.read()),
                _headers={'Content-Type': 'image/png'}
            )

        line_bot_api.set_default_rich_menu(rich_menu_id=rich_menu_a_id)

        # 7. Create rich menu alias A
        alias_a = CreateRichMenuAliasRequest(
            rich_menu_alias_id='richmenu-alias-a',
            rich_menu_id=rich_menu_a_id
        )
        line_bot_api.create_rich_menu_alias(alias_a)

        print('success')


main()
