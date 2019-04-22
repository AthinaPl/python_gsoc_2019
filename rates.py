#!/usr/bin/env python3
import sys
import subprocess
import requests
import argparse
import datetime
import json

def input_args():

    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-b", "--base", required=True,
            help="The base currency to convert from, required")
    parser.add_argument(
            "-c", "--currency", action='append', default=[], required=True,
            help="the currency to convert to, required, can be specified multiple times, use the option once per currency ID")
    parser.add_argument(
            "-d", "--date", nargs=1,
            help="The date of the exchange rates in format YYYY-MM-DD, optional, if it's not specified the current date is used")
    parser.add_argument(
            "N", metavar='N', type=float, nargs='*',
            help="Number which will be converted, required, can be specified multiple times, using spaces between input values")
    args = parser.parse_args()

    return args


def get_response(in_base, in_cur, in_date):

    api_url_base = 'https://api.exchangeratesapi.io/{dt}?base={bs}&symbols={cr}'.format(dt=in_date, bs=in_base, cr=in_cur)

    ret = requests.get(api_url_base).json()
    if "error" in ret:
        # https://www.exchangerate-api.com/docs/documentation error responses from the API documentation are not correct
        raise Exception(ret["error"])
    else:
        return ret

def validate_date(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")

def check_positive(value):
    if value <= 0.0:
        raise argparse.ArgumentTypeError("A positive value was expected, got %s instead" % value)

def convert(base, currency, value, date=None):
    """
    Converts @value from @base currency to desired @currency.
    There is option @date argument where user can set specific
    date to get the exchange rates, otherwise current date is used.

    @base and @currency accepts mix of lowercase and uppercase, if
    user provides currency that doesn't exists raise RuntimeError.

    If value cannot be converted to float raise RuntimeError.

    If date is not provided in format YYYY-MM-DD raise RuntimeError.

    Returns converted value.
    """
    base = base.upper()

    if not date:
        today = datetime.datetime.now()
        in_date = today.strftime("%Y-%m-%d")
    else:
        validate_date(date[0])
        in_date = date[0]

    if len(value) != len(currency):
        raise Exception("More currencies supplied than values to convert")

    # Open file for caching
    filepath = 'cachefile.txt'
    
    # Go over all elements of the currency array since we accept multiple currencies for convesion
    for index in range(len(currency)):
        check_positive(value[index])
        currency[index] = currency[index].upper()
        # The API answer looks like this
        # {"base": "EUR", "rates": {"USD": xxxx}, "date": "2019-04-18"}
        with open("cachefile.txt", "a+") as cachefile:
            cachefile.seek(0, 0)
            for line in cachefile:
                json_line = json.loads(line)

                if json_line["base"] == base and currency[index] in json_line["rates"].keys() and json_line["date"] == in_date:
                    print("Found in cache!")
                    re = json_line
                    break
            else: # not found
                re = get_response(base, currency[index], in_date)
                line_to_search = json.dumps(re)
                cachefile.write(line_to_search + "\n") # append missing data

        # Parse the conversion rate out of the returned dictionary
        conv_rate = re['rates'][currency[index]]

        # Print result
        print("{} {} is {} {}".format(value[index], base, conv_rate*value[index], currency[index]))


if __name__ == '__main__':

    args = input_args()

    convert(args.base, args.currency, args.N, args.date)
