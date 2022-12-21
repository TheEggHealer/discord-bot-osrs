import discord
from discord.ext import commands
import price_calc as pc
import pandas as pd

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
  print('Logged in')

  

@client.event
async def on_message(message):
  # print(message)
  if message.author == client.user:
    return
  
  if message.content.startswith('!help'):
    await message.channel.send('''How to use:
!flip <item_id> - Item flip stats
!flipg <item_id> - Item flip stats and price history graph
!set <set_piece1> <set_piece2> ... <completed> - Profit from combining pieces''')

  elif message.content.startswith('!flip '):
    try:
      segments = message.content.split(' ')
      item_id = segments[1]
      time = int(segments[2]) * 60 * 60 if len(segments) > 2 else 3600
      response = pc.item_stats(int(item_id), time_filter=time, plot=False, verbose=True)
      await message.channel.send(response)
    except:
      await message.channel.send('No item found with that id.')

  elif message.content.startswith('!flipg '):
    try:
      segments = message.content.split(' ')
      item_id = segments[1]
      time = int(segments[2]) * 60 * 60 if len(segments) > 2 else 3600
      response = pc.item_stats(int(item_id), time_filter=time, plot=True, verbose=True)
      embed = discord.Embed()
      img_file = None

      img_file = discord.File(open('tmp_avg_price.png', 'rb'))
      embed.set_image(url="attachment://tmp_avg_price.png")

      await message.channel.send(response, embed=embed, file=img_file)
    except:
      await message.channel.send('No item found with that id.')

  elif message.content.startswith('!set '):
    segments = message.content.split(' ')
    piece_ids = segments[1:len(segments) - 1]
    completed_id = segments[len(segments) - 1]
    response = pc.set_price(piece_ids, completed_id)

    await message.channel.send(response)
  
  elif message.content.startswith('!adv'):
    try:
      segments = message.content.split(' ')
      item_id = segments[1]
      time_step = segments[2] if len(segments) > 1 else '5m'
      time_filter = None
      if len(segments) > 2: time_filter = segments[3]
      
      response = pc.adv_graph(int(item_id), time_step=time_step, time_filter=int(time_filter))
      embed = discord.Embed()
      img_file = None

      img_file = discord.File(open('adv.png', 'rb'))
      embed.set_image(url="attachment://adv.png")

      await message.channel.send('Detailed graph', embed=embed, file=img_file)
    except Exception as e:
      await message.channel.send(f'Something went wrong. Error: {e}')
  
  elif message.content.startswith('!store'):
    try:
      segments = message.content.split(' ')
      response = ''
      
      if segments[1] == 'all':
        response = pc.store_list()
      else:
        response = pc.store_item_data(int(segments[1]))
      
      await message.channel.send(response)
    except Exception as e:
      await message.channel.send(f'Something went wrong. Error: {e}')

  elif message.content.startswith('!add '):
    segments = message.content.split(' ')
    item_id = int(segments[1])
    item_name = ' '.join(segments[2:])

    with open('items.txt', mode='r+') as file:
      items = file.read().strip().split('\n')
      items.append(f'{item_id}\t{item_name}')
      items = list(set(items))
      file.seek(0)
      file.write('\n'.join(items))

    await message.channel.send(f'Added {item_name} to the list.')
  
  elif message.content.startswith('!list'):
    with open('items.txt', mode='r+') as file:
      await message.channel.send(f'{file.read()}')

  elif message.content.startswith('!rank'):
    await message.channel.send('Working on it...')
    alg = message.content.split(' ')[1]
    with open('items.txt', mode='r+') as file:
      file_lines = file.read().strip().split('\n')
      items = []
      for line in file_lines:
        item_id = line.split('\t')[0]
        item_name = line.split('\t')[1]

        stats_day = pc.item_stats(item_id, time_filter=24 * 60 * 60, verbose=False)
        stats_one = pc.item_stats(item_id, time_filter=60 * 60, verbose=False)

        items.append([item_id, item_name, stats_one, stats_day])

      if alg == 'variance': 
        items.sort(key=lambda i: -i[2]['variance'] / i[3]['variance'])
      elif alg == 'profit1':
        items.sort(key=lambda i: -i[2]['expected_gold_per_hour'])
      elif alg == 'profit24':
        items.sort(key=lambda i: -i[3]['expected_gold_per_hour'])
      elif alg == 'std':
        items.sort(key=lambda i: -(i[2]['std_dev'] * 2 - 0.01 * i[2]['sell_price']))
      response_lines = []

      for item in items[:5]:
        text = ''
        if alg == 'variance':
          val = item[2]['variance'] / item[3]['variance']
          text = f'{round(val, 3)}'
        elif alg == 'profit1':
          profit = item[2]['expected_gold_per_hour']
          text = f'{profit:,} gp / h'
        elif alg == 'profit24':
          profit = item[3]['expected_gold_per_hour']
          text = f'{profit:,} gp / h'
        elif alg == 'std':
          val = item[2]['std_dev'] * 2 - 0.01 * item[2]['sell_price']
          text = f'{round(val):,} after tax'

        response_lines.append(f'{item[0]}, {item[1]}: **{text}**')

      response_lines = '\n'.join(response_lines)
      await message.channel.send(f'{response_lines}')


client.run('MTA0NTc5MDExOTQ1MTQzNTE0MA.Gb5Qpo.bJs6behloRiK5lm0rHGq59gYFonLvGDYtdvJ7I')