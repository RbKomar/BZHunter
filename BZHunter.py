import requests
import math
import numpy as np
import pandas as pd

API_KEY = 'xxx'

item_map = {"WATER_LILY": "lily_pad", "INK_SACK:3": "ink_sack", "INK_SACK:4": "enchanted_ink_sack",
            "CARROT_ITEM": "carrot",
            "ENCHANTED_ENDSTONE": "enchanted_end_stone", "ENCHANTED_SLIME_BALL": "enchanted_slimeball",
            "ENCHANTED_BROWN_MUSHROOM": "enchanted_red_mushroom", "PROTECTOR_FRAGMENT": "protector_dragon_fragment",
            "WISE_FRAGMENT": "wise_dragon_fragment",
            "POTATO_ITEM": "potato", "ENCHANTED_HUGE_MUSHROOM_1": "enchanted_red_mushroom_block",
            "ENCHANTED_HUGE_MUSHROOM_2": "enchanted_brown_mushroom_block",
            "HUGE_MUSHROOM_1": "red_mushroom_block", "HUGE_MUSHROOM_2": "brown_mushroom_block",
            "STRONG_FRAGMENT": "strong_dragon_fragment",
            "SLIME_BALL": "slimeball", "SNOW_BALL": "snowball", "ENCHANTED_COCOA": "enchanted_cocoa_beans",
            "HAY_BLOCK": "hay_bale", "ENCHANTED_NETHER_STALK": "mutant_nether_stalk",
            "ENCHANTED_CARROT_STICK": "enchanted_carrot_on_a_stick", "YOUNG_FRAGMENT": "young_dragon_fragment",
            "ENCHANTED_WATER_LILY": "enchanted_lily_pad",
            "UNSTABLE_FRAGMENT": "unstable_dragon_fragment", "ENCHANTED_CLAY_BALL": "enchanted_clay",
            "ENCHANTED_HAY_BLOCK": "enchanted_hay_bale",
            "SUPER_EGG": "super_enchanted_egg", "SUPERIOR_FRAGMENT": "superior_dragon_fragment", "CLAY_BALL": "clay",
            "OLD_FRAGMENT": "old_dragon_fragment",
            "ENDER_STONE": "end_stone", "RABBIT": "raw_rabbit", "NETHER_STALK": "nether_wart", "SULPHUR": "gunpowder",
            "ENCHANTED_RABBIT": "enchanted_raw_rabbit",
            "PORK": "raw_porkchop"}


def remove_outliers(data):
    data = pd.DataFrame(data)
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1

    df = data[~((data < (Q1 - 1.5 * IQR)) | (data > (Q3 + 1.5 * IQR))).any(axis=1)]
    df = df.to_numpy()
    return df


def get_past_prices(item: str):
    header = {
        "scheme": "https",
        "method": "GET",
        "authority": "api.bazaartracker.com",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="92"',
        "accept": "application/json, text/javascript, */*; q=0.01",
        "sec-ch-ua-mobile": "0",
        "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
        "origin": "https://bazaartracker.com",
        "sec-fetch-site": 'same-site',
        "sec-fetch-mode": 'cors',
        "sec-fetch-dest": 'empty',
        "referer": 'https://bazaartracker.com/',
        "accept-encoding": 'gzip, deflate',
        "accept-language": 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    api_bazaar_site = 'http://api.bazaartracker.com/product/' + item.lower()
    response = requests.get(api_bazaar_site, headers=header, params={"token": 'No'})
    response = response.json()
    if not response["success"]:
        if item in item_map.keys():
            if item_map[item] == "err":
                print("Error with the item: ", item)
                return 0, 0
            return get_past_prices(item_map[item])
        else:
            print("Failed for: ", item)
            return 0, 0
    avg_prices_history = response["avgHistory"]
    buy_prices = []
    sell_prices = []
    for price in avg_prices_history:
        buy_prices.append(price["buyAvg"])
        sell_prices.append(price["sellAvg"])
    return buy_prices, sell_prices


def get_averaged_prices(item: str):
    buy_prices, sell_prices = get_past_prices(item)
    if buy_prices == 0:
        print("Failed getting past prices for: ", item)
        return 0, 100000000, 0, 10000000000, -1
    buy_prices = remove_outliers(np.array(buy_prices))
    sell_prices = remove_outliers(np.array(sell_prices))

    averaged_last_week_profit = (buy_prices.sum() - sell_prices.sum()) / len(buy_prices)
    buy_avg = np.average(buy_prices)
    sell_avg = np.average(sell_prices)
    buy_std = np.std(buy_prices)
    sell_std = np.std(sell_prices)
    return buy_avg, buy_std, sell_avg, sell_std, averaged_last_week_profit


def put_averaged_past_prices_to_csv():
    api_bazaar_url = 'https://api.hypixel.net/skyblock/bazaar'
    response = requests.get(api_bazaar_url, API_KEY)
    response = response.json()
    file = open('objects.txt', 'w')
    object_names = []
    for object_name in response["products"]:
        object_names.append(object_name)
        file.write(object_name + '\n')
    file.close()
    averaged_past_prices = {}
    for object_name in object_names:
        buy_avg, buy_std, sell_avg, sell_std, last_week_profit_avg = get_averaged_prices(object_name)
        averaged_past_prices[object_name] = [buy_avg, buy_std, sell_avg, sell_std, last_week_profit_avg]
    averaged_past_prices = pd.DataFrame(averaged_past_prices)
    averaged_past_prices.to_csv("averaged_past_prices.csv")


def get_averaged_past_prices_from_csv():
    filename = "averaged_past_prices.csv"
    return pd.read_csv(filename)


def get_uuid(username: str):
    api_uuid = 'https://api.hypixel.net/player'
    parameters = {"key": API_KEY, "name": username}
    response = requests.get(api_uuid, params=parameters).json()
    print(response['player']['uuid'])


def get_purse(player: str):
    api_profile_id = 'https://api.hypixel.net/skyblock/profiles'
    UUID = get_uuid(player)
    parameters = {"key": API_KEY, "uuid": UUID}
    response = requests.get(api_profile_id, params=parameters)
    response = response.json()
    return response['profiles'][0]['members'][UUID]['coin_purse']


def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def get_best_bazaar_flips(username, get_past=False):
    api_bazaar_url = 'https://api.hypixel.net/skyblock/bazaar'
    response = requests.get(api_bazaar_url, API_KEY)
    response = response.json()
    file = open('objects.txt', 'w')
    object_names = []
    for object_name in response["products"]:
        object_names.append(object_name)
        file.write(object_name + '\n')
    file.close()
    purse = get_purse(username)
    flips = []
    past_averaged_prices = get_averaged_past_prices_from_csv()
    for object_name in object_names:
        current_item = {"item_name": object_name, "outlier": False}
        if get_past:
            buy_avg, buy_std, sell_avg, sell_std, last_week_profit_avg = get_averaged_prices(object_name)
        else:
            buy_avg, buy_std, sell_avg, sell_std, last_week_profit_avg = past_averaged_prices[object_name]
        sell_summary = response["products"][object_name]['sell_summary']
        buy_summary = response["products"][object_name]['buy_summary']
        quick_status = response["products"][object_name]['quick_status']
        if len(sell_summary) == 0 or len(buy_summary) == 0:
            print("Empty orders list in: " + object_name)
            continue
        if quick_status['buyMovingWeek'] < 1000000 or quick_status['sellMovingWeek'] < 1000000:
            continue
        buy_price = sell_summary[0]['pricePerUnit'] + 0.1
        if not (buy_avg - 1 * buy_std < buy_price < buy_avg + 1 * buy_std) or buy_price == 0:
            current_item["outlier"] = True
        sell_price = buy_summary[0]['pricePerUnit'] - 0.1
        if not (sell_avg - 1 * sell_std < sell_price < sell_avg + 1 * sell_std):
            current_item["outlier"] = True
        else:
            buy_amount = math.floor(purse / buy_price)
            if buy_amount > 70000:
                buy_amount = 70000
            profit = math.floor((sell_price - buy_price) * buy_amount)
            current_item['buyPrice'] = buy_price
            current_item['sellPrice'] = sell_price
            current_item['profit'] = profit
            current_item['buyAmount'] = buy_amount
            current_item['buyMovingWeek'] = quick_status['buyMovingWeek']
            current_item['sellMovingWeek'] = quick_status['sellMovingWeek']
            current_item['last_week_profit_avg'] = last_week_profit_avg * buy_amount
            flips.append(current_item)

    # saving the flips by order of most profit
    flips = sorted(flips, key=lambda x: x['profit'], reverse=True)
    file = open('best_flips_v2.txt', 'w')
    for flip in flips:
        file.write(str(flip['item_name']) + " with profit of " + human_format(flip['profit'])
                   + " buying quantity of " + human_format(flip['buyAmount']) +
                   " while insta-buys/7d " + human_format(flip['buyMovingWeek']) +
                   " and insta-sells/7d " + human_format(flip['sellMovingWeek']) +
                   " //price: b" + human_format(flip['buyPrice']) + "/s" + human_format(flip['sellPrice']) +
                   " and last week averaged profit: " + human_format(flip["last_week_profit_avg"]) +
                   " //outlier: " + str(flip["outlier"]) + '\n')
    file.close()


if __name__ == '__main__':
    player = 'xxx'
    # while get_prices_history is True, script collects the history of prices
    # use it once in a while then change to False (like once a day)
    get_prices_history = True
    get_best_bazaar_flips(player, get_prices_history)
