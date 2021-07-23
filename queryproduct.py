import requests
import pandas as pd
from IPython.display import Image, HTML

AUTH_KEY = 'qhqws47nyvgze2mq3qx4jadt'
DECODE_URL = 'https://api.bestbuy.com/v1/'
AUTH_URL = f'apiKey={AUTH_KEY}&format=json'


def parse_data(product):
    words = product.split()
    SEARCH_URL = f'products('
    for word in words:
        SEARCH_URL += f'search={word}&'

    RESULT_URL = ''

    for i in range(len(SEARCH_URL) - 1):
        RESULT_URL += SEARCH_URL[i]

    RESULT_URL += ')?show=thumbnailImage,name,salePrice,addToCartUrl,'
    RESULT_URL += 'sku&pageSize=10&active=true&'

    decoder = requests.get(DECODE_URL + RESULT_URL + AUTH_URL)
    
    if(decoder.status_code == 200):
    
        decoder = decoder.json()

        df = pd.json_normalize(decoder['products'])

        df['thumbnailImage'] = df['thumbnailImage']\
            .str.replace(
            '(.*)',
            '<img src="\\1" style="max-height:248px;"></img>'
        )

        df['addToCartUrl'] = df['addToCartUrl']\
            .str.replace(
            '(.*)',
            '<a href="\\1">Add to Cart</a>'
        )

        df.sku = df.sku.astype('str')

        df['sku'] = df['sku']\
            .str.replace(
            '(.*)',
            '<a href="item/\\1">Alternatives</a>'
        )

        df.columns = ['Image', 'Product', 'Price', 'Purchase', 'Alternatives']

        print('Search results:')
        print(df)
        return df
    
    return None


def get_product_info(sku):
    PRODUCT_URL = f'products/{sku}.json?show=all&'
    decoder = requests.get(DECODE_URL + PRODUCT_URL + AUTH_URL)
    if decoder.status_code == 200:
        decoder = decoder.json()
        df = pd.json_normalize(decoder)
        return decoder
    
    return None


def find_alts(sku, product_price):
    PRODUCT_URL = f'products/{sku}/alsoViewed?'
    decoder = requests.get(DECODE_URL + PRODUCT_URL + AUTH_URL)
    
    if decoder.status_code == 200:
        decoder = decoder.json()


        FIELDS = ['sku', 'prices.current', 'links.addToCart']

        df = pd.json_normalize(decoder['results'])
        df = df[FIELDS]
        df = df[df['prices.current'] <= product_price]

        if df.empty:
            print('No cheaper alternatives found.')
            return df

        print('Cheaper alternatives:')
        print(df)
        return df
    
    return None


def main():
    product = input("Search for a product: ")
    manufacturer = input("Who manufactures it? Enter: ")
    resultDF = parse_data(product, manufacturer)
    sku = input("Enter desired SKU: ")
    sku = int(sku)
    resultDF = resultDF[resultDF['sku'] == sku]
    product_price = resultDF.iloc[0]['salePrice']
    alts = find_alts(sku, product_price)


if __name__ == "__main__":
    main()
