import enum
from collections import namedtuple


class GameOptions:
    PredefinedOptions = namedtuple('PredefinedOptions', ['app_id', 'context_id'])

    STEAM = PredefinedOptions('753', '6')
    DOTA2 = PredefinedOptions('570', '2')
    CS = PredefinedOptions('730', '2')
    TF2 = PredefinedOptions('440', '2')
    PUBG = PredefinedOptions('578080', '2')
    RUST = PredefinedOptions('252490', '2')

    def __init__(self, app_id: str, context_id: str) -> None:
        self.app_id = app_id
        self.context_id = context_id


class Asset:
    def __init__(self, asset_id: str, game: GameOptions, amount: int = 1, name = '') -> None:
        self.asset_id = asset_id
        self.game = game
        self.amount = amount
        self.name = name
    def to_dict(self):
        return {
            'appid': int(self.game.app_id),
            'contextid': self.game.context_id,
            'amount': self.amount,
            'assetid': self.asset_id
        }


class Currency(enum.IntEnum):
    USD = 1
    GBP = 2
    EURO = 3
    CHF = 4
    RUB = 5
    UAH = 18

class TradeOfferState(enum.IntEnum):
    Invalid = 1
    Active = 2
    Accepted = 3
    Countered = 4
    Expired = 5
    Canceled = 6
    Declined = 7
    InvalidItems = 8
    ConfirmationNeed = 9
    CanceledBySecondaryFactor = 10
    StateInEscrow = 11


class SteamUrl:
    API_URL = "https://api.steampowered.com"
    COMMUNITY_URL = "https://steamcommunity.com"
    STORE_URL = 'https://store.steampowered.com'


class Endpoints:
    CHAT_LOGIN = SteamUrl.API_URL + "/ISteamWebUserPresenceOAuth/Logon/v1"
    SEND_MESSAGE = SteamUrl.API_URL + "/ISteamWebUserPresenceOAuth/Message/v1"
    CHAT_LOGOUT = SteamUrl.API_URL + "/ISteamWebUserPresenceOAuth/Logoff/v1"
    CHAT_POLL = SteamUrl.API_URL + "/ISteamWebUserPresenceOAuth/Poll/v1"
