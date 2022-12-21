import requests as req
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import time
import os

def item_stats(id, time_filter=3600, plot=False, descrete=True, verbose=False):
  headers = {
    'User-Agent': 'python-requests',
  }

  data_json = req.get(f'https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=5m&id={id}', headers=headers).json()
  df = pd.json_normalize(data_json['data'])

  # time_filter = 3600
  filtered_high_vol = np.array([val for index, val in enumerate(df['highPriceVolume']) if df['timestamp'][index] > int(time.time()) - time_filter])
  filtered_low_vol = np.array([val for index, val in enumerate(df['lowPriceVolume']) if df['timestamp'][index] > int(time.time()) - time_filter])
  filtered_high_price = np.array([val for index, val in enumerate(df['avgHighPrice']) if df['timestamp'][index] > int(time.time()) - time_filter])
  filtered_low_price = np.array([val for index, val in enumerate(df['avgLowPrice']) if df['timestamp'][index] > int(time.time()) - time_filter])
  filtered_timestamps = np.array([val for val in df['timestamp'] if val > int(time.time()) - time_filter])

  total_sold = sum(filtered_high_vol) + sum(filtered_low_vol)
  high_vol = filtered_high_vol
  low_vol = filtered_low_vol
  # avg_high_price = np.mean(df['avgHighPrice'])
  # avg_low_price = np.mean(df['avgLowPrice'])
  # avg_price_array = (df['avgHighPrice'] + df['avgLowPrice']) / 2
  avg_price_array = (np.nan_to_num(filtered_high_price * high_vol, nan=0) + np.nan_to_num(filtered_low_price * low_vol, nan=0)) / (high_vol + low_vol)
  avg_price = np.mean(avg_price_array)
  variance = np.var(avg_price_array)
  std_dev = np.sqrt(variance)
  # avg_price = (avg_high_price + avg_low_price) / 2

  time_diff = int(time.time()) - (filtered_timestamps[0])
  time_diff_hours = (time_diff / 60) / 60

  low_25 = np.quantile(avg_price_array, 0.25)
  high_25 = np.quantile(avg_price_array, 0.75)

  buy_price = round(low_25) if descrete else avg_price - low_25
  sell_price = round(high_25) if descrete else high_25
  
  # message = f'''Item id: {id} 
  #   Avg. High Price: {avg_high_price} 
  #   Avg. Low Price: {avg_low_price} 
  #   Avg. Price: {avg_price} 
  #   Variance: {variance} 
  #   Std. dev: {std_dev} 
  #   Time: {time_diff} seconds, {time_diff_hours} hours 
  #   Total Sold: {total_sold}, Sold / h: {total_sold / time_diff_hours}
    
  #   Rec. buy price: {buy_price} 
  #   Rec. sell price: {sell_price} 
  #   Expected. diff: {sell_price - buy_price} 
  #   Expected. diff after tax: {sell_price * 0.99 - buy_price} 
  #   Expected sold / h: {0.158 * (total_sold / time_diff_hours)} 
  #   Expected gp / h: {(sell_price * 0.99 - buy_price) * (0.158 * (total_sold / time_diff_hours))} 
  # '''

  message =   f'''Item id: **{id}** 
Avg. Price: **{round(avg_price):,}**
Total Sold: **{total_sold:,} ({round(total_sold / time_diff_hours, 2):,} / h)**
Time: **{round(time_diff_hours)} hours**

Rec. buy price: **{buy_price:,}** 
Rec. sell price: **{sell_price:,}** 
Expected profit after tax: **{round(sell_price * 0.99 - buy_price):,} / item** 
Expected sold: **{round(0.158 * (total_sold / time_diff_hours), 2):,} / h** 
Expected profit: **{round((sell_price * 0.99 - buy_price) * (0.158 * (total_sold / time_diff_hours))):,} gp / h** 
'''
  
  if plot:
    plt.figure()
    plt.plot(avg_price_array)
    plt.savefig('tmp_avg_price.png')

  if verbose:
    return message

  else:
    return {
      'id': id,
      'variance': variance,
      'avg_price': avg_price,
      'buy_price': buy_price,
      'sell_price': sell_price,
      'diff': sell_price - buy_price,
      'diff_tax': sell_price * 0.99 - buy_price,
      'sold_volume': total_sold / time_diff_hours,
      'expected_sell_volume': 0.158 * (total_sold / time_diff_hours),
      'expected_gold_per_hour': round((sell_price * 0.99 - buy_price) * (0.158 * (total_sold / time_diff_hours))),
      'avg_price_array': avg_price_array,
      'std_dev': std_dev
    }










def set_price(pieces_ids, completed_set):

    headers = {
        'User-Agent': 'python-requests',
    }

    data_frames = []
    for _id in pieces_ids:
        data_json = req.get(f'https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=5m&id={_id}', headers=headers).json()
        df = pd.json_normalize(data_json['data'])
        data_frames.append(df)
    
    data_json = req.get(f'https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep=5m&id={completed_set}', headers=headers).json()
    data_frame_completed  = pd.json_normalize(data_json['data'])
    
    avg_prices_pieces = np.array([(np.nan_to_num(df['avgHighPrice'] * df['highPriceVolume'], nan=0) + np.nan_to_num(df['avgLowPrice'] * df['lowPriceVolume'], nan=0)) / (df['highPriceVolume'] + df['lowPriceVolume']) for df in data_frames])
    avg_price_completed = (np.nan_to_num(data_frame_completed['avgHighPrice'] * data_frame_completed['highPriceVolume'], nan=0) + np.nan_to_num(data_frame_completed['avgLowPrice'] * data_frame_completed['lowPriceVolume'], nan=0)) / (data_frame_completed['highPriceVolume'] + data_frame_completed['lowPriceVolume'])

    # print(sum(avg_prices_pieces.mean(axis=1)))

    diff = avg_price_completed.mean() * 0.99 - sum(avg_prices_pieces.mean(axis=1))

    return f'''Pieces price: **{round(sum(avg_prices_pieces.mean(axis=1)))}**
Completed price after tax: **{round(avg_price_completed.mean() * 0.99)}**
Diff: **{round(diff)}**'''


#############################################

HEADERS = {
  'User-Agent': 'python-requests',
}

def get_data(item_id, time_step='5m', time_filter=None):
  data_json = req.get(f'https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep={time_step}&id={item_id}', headers=HEADERS).json()
  df = pd.json_normalize(data_json['data'])
  df = df[::-1].reset_index(drop=True) # Reverse data

  if time_filter:
    df = df[df['timestamp'] > int(time.time()) - time_filter]

  high_vol = np.nan_to_num(df['highPriceVolume'], nan=0)
  low_vol = np.nan_to_num(df['lowPriceVolume'], nan=0)
  avg_high_price_array = np.nan_to_num(df['avgHighPrice'], nan=0)
  avg_low_price_array = np.nan_to_num(df['avgLowPrice'], nan=0)
  avg_price_array = (avg_high_price_array * high_vol + avg_low_price_array * low_vol) / (high_vol + low_vol)
  avg_high_price = np.mean(avg_high_price_array)
  avg_low_price = np.mean(avg_low_price_array)
  avg_price = np.mean(avg_price_array)
  variance = np.var(avg_price_array)
  std_dev = np.sqrt(variance)
  total_sold = sum(high_vol) + sum(low_vol)
  
  time_stamps = df['timestamp']
  time_diff = time_stamps[len(time_stamps) - 1] - time_stamps[0]
  time_diff_hours = (time_diff / 60) / 60

  return {
    'high_vol': high_vol,
    'low_vol': low_vol,
    'avg_high_price_array': avg_high_price_array,
    'avg_low_price_array': avg_low_price_array,
    'avg_price_array': avg_price_array,
    'avg_high_price': avg_high_price,
    'avg_low_price': avg_low_price,
    'avg_price': avg_price,
    'variance': variance,
    'std_dev': std_dev,
    'total_sold': total_sold,
    'time_stamps': time_stamps,
    'time_diff': time_diff,
    'time_diff_hours': time_diff_hours,
    'df': df
  }

def adv_graph(item_id, time_step='5m', time_filter=None):
  ITEM_ID = item_id
  TIME_STEP = time_step
  FIT_DEGREE = 4
  TIME_FILTER = time_filter * 3600

  item_data = get_data(ITEM_ID, time_step=TIME_STEP, time_filter=TIME_FILTER)

  plt.figure(figsize=(16, 6))

  ################################################################### FIGURE 1

  plt.subplot(1, 2, 1);
  plt.title('Price history')

  x = np.linspace(0, item_data['time_diff_hours'], len(item_data['avg_price_array']))
  plt.plot(x, item_data['avg_price_array'], '-', label='price');

  poly_fit = np.polyfit(x, item_data['avg_price_array'], FIT_DEGREE)
  p = np.poly1d(poly_fit)
  plt.plot(x, p(x), 'r--', label=f'deg. {FIT_DEGREE} fit');
  poly_fit = np.polyfit(x, item_data['avg_price_array'], 1)
  p = np.poly1d(poly_fit)
  plt.plot(x, p(x), '-', label='deg. 1 fit');

  plt.plot(x, np.full((len(x)), item_data['avg_price'] + item_data['std_dev']), 'g-.', label='1 std');
  plt.plot(x, np.full((len(x)), item_data['avg_price'] - item_data['std_dev']), 'g-.');

  avg_n = 20
  high_avg = sum(sorted(item_data['avg_price_array'])[:avg_n]) / avg_n
  plt.plot(x, np.full(len(x), high_avg), linestyle=(0, (3, 1, 1, 1)), color='indigo', label='flip')

  low_avg = sum(sorted(item_data['avg_price_array'])[-avg_n:]) / avg_n
  plt.plot(x, np.full(len(x), low_avg), linestyle=(0, (3, 1, 1, 1)), color='indigo')

  # plt.legend(['price', f'deg. {FIT_DEGREE} fit', 'deg. 1 fit', '1 std', None, 'buy']);
  plt.legend();

  ################################################################### FIGURE 2

  plt.subplot(1, 2, 2);
  plt.title('Trade volume')

  x = (np.arange(len(item_data['high_vol'])) / len(item_data['high_vol'])) * item_data['time_diff_hours']
  width = item_data['time_diff_hours'] / len(x)
  plt.bar(x, item_data['high_vol'], width=width, bottom=item_data['low_vol']);
  plt.bar(x, item_data['low_vol'], width=width);


  plt.legend(['high price vol.', ' low price vol.']);

  plt.savefig('adv.png')

def store_item_data(item_id):
  FILE_NAME = f'stored/item_{item_id}.dat'

  item_data = get_data(item_id, time_step='5m')

  data_frame = item_data['df']

  response = ''

  if os.path.isfile(FILE_NAME):
    old = pd.read_pickle(FILE_NAME)
    latest_time = old['timestamp'][0]

    new_entries = data_frame[data_frame['timestamp'] > latest_time]

    response = f'Added {len(new_entries)} entries to {FILE_NAME}.'

    data_frame = pd.concat([new_entries, old], ignore_index=True)
  else:
    response = f'Created file: {FILE_NAME} and stored {len(data_frame)} entries.'

  pd.to_pickle(data_frame, FILE_NAME)
  return response

def store_list():
  with open('items.txt', mode='r+') as file:
    file_lines = file.read().strip().split('\n')
    responses = []

    for line in file_lines:
      item_id = line.split('\t')[0]
      responses.append(store_item_data(item_id))
    
    return '\n'.join(responses)
      