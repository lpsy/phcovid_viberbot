import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from time import sleep
import os
import json

    
if __name__ == '__main__':
    worldometerURL = 'https://www.worldometers.info/coronavirus/country/philippines/'
    
    date_today = datetime.utcnow()+timedelta(hours=8)
    newsId = f'#newsdate{date_today.strftime("%Y-%m-%d")}'

    # re-try if error
    for i in range(12):
        try:
            resp = requests.get(worldometerURL)

            soup = BeautifulSoup(resp.text, features="html.parser")

            infected, deaths, recovered = [
                x.text.strip() for x in soup.select(
                    '#maincounter-wrap .maincounter-number span')
            ]
            hist_path = '/home/ubuntu/viber_flask/covid_history.txt'
            mode = 'r+' if os.path.exists(hist_path) else 'w'

            with open(hist_path, mode) as fp:
                if mode == 'r+':
                    history = fp.readlines()
                    latest = history[-1].split(', ')
                    if (
                        (infected==latest[1]) 
                        and (deaths==latest[2])
                        and (recovered==latest[3])
                        ):

                        send = False
                    else:
                        d_infected = (int(infected.replace(',', ''))
                                      -int(latest[1].replace(',', '')))
                        d_deaths = (int(deaths.replace(',', ''))
                                    -int(latest[2].replace(',', '')))
                        d_recovered = (int(recovered.replace(',', ''))
                                       -int(latest[3].replace(',', '')))
                        send = True
                else:
                    send = True
                if send:
                    try:
                        news = soup.select(
                            f'{newsId} .news_body ul li strong')[0].text
                        news_source = soup.select(
                            f'{newsId} .news_body ul li span a')[0].get('href')
                    except:
                        news = ''
                        news_source = ''

                    active = (int(infected.replace(',', '')) - int(deaths.replace(',', '')) - int(recovered.replace(',', '')))
    
                    message = (f'{date_today.strftime("%Y-%m-%d %H:%M")}\n'
                               f'Infected: {infected} ({d_infected:+d})\n'
                               f'Deaths: {deaths} ({d_deaths:+d})\n'
                               f'Recovered: {recovered} ({d_recovered:+d})\n'
                               f'\n'
                               f'Active Cases: {active:,.0f}\n\n'
                               f'source: {news_source}'
                              )

                    with open('tokens.json') as fp:
                        code = json.load(fp)['post_request']
                        webhook_url = json.load(fp)['webhook_url']
                    requests.post(webhook_url,
                     json=json.dumps({'message':message, 'code':code}))

                    fp.write(
                        f'{date_today}, {infected}, {deaths},'
                        f' {recovered}, {news}, {news_source}\n')

                else:
                    print(f'No updates as of {date_today}')
            break
        except Exception as e:
            print(date_today, e)
            print(f'{date_today} Failed to load data, retrying ({i+1})...')
            sleep(5)