import os
import json
from datetime import datetime
from django.utils import timezone
from gradio_client import Client, handle_file
from django.conf import settings

def parse_receipt_text(image_url: str):
    """
    영수증 이미지를 파싱하여 구조화된 데이터를 반환합니다.
    
    Args:
        image_url (str): 영수증 이미지 URL
        
    Returns:
        dict: 파싱된 영수증 데이터
    """
    try:
        # API 클라이언트 초기화
        client = Client("valenynl/ReceiptSplitAI")
        
        # API 호출
        try:
            # API 호출
            result = client.predict(
                input_image=handle_file(image_url),
                model_name="gemini-1.5-flash",
                prompt_name="prompt_v1",
                temperatura=0,
                system_instruction="You are receipts recognizer",
                current_prompt_text="""Task: Accurately extract structured information from receipt images and return it in a standardized JSON format. Ensure high accuracy even when receipts vary in format, language (including non-Latin scripts), and layout. Handle challenges like text noise, multiple lines for item names, and potential gaps in information.

Receipts: May be in various languages (Latin and non-Latin scripts), in diverse formats, and may contain noise like logos, faded text, or watermarks.

Output Format: Return the output as a JSON object with the following structure:

{
    "store_name": string,  -- Exact name of the store as found on the receipt. It`s not always the bigger text. Find the correct name of the shop/restaurant
    "country": string,  -- Define country if available; otherwise, "unknown". Identify country by details on the receipt. Use receipt address or language if explicit country info is lacking.
    "receipt_type": string,  -- Define receipt type (e.g. Restaurant/Shop/Other) if available; otherwise, "unknown"
    "address": string,  -- Full address, if available; otherwise, "unknown"
    "datetime": "YYYY.MM.DD HH:MM:SS",  -- Convert all date formats to this standard
    "currency": string,  -- Currency code (e.g., "EUR", "USD", "UAH") based on the detected currency symbol. Don`t put here currency symbol, only code.
    "sub_total_amount": 0.00,  -- This represents the total cost of all items and services on the receipt before any tips, or additional charges are applied. If sub_total_amount is not present on the receipt, set "unknown"
    "total_price": 0.00,  -- The final total amount from the receipt (in the majority of situations this one is bigger then other values + it could be as bold font). The total amount may not always be the largest number; ensure the context is understood from surrounding text.
    "total_discount": 0.00,  -- Total discount applied based on individual item discounts or explicit discount information
    "all_items_price_with_tax": True/False -- Indicates whether taxes are included in the prices of items. Set to True if taxes are included, False if they are not included. If it cannot be determined, set to "unknown".
    "payment_method": "card", "cash", or "unknown",  -- Detect payment method based on keywords like "card", "cash", "master card", "visa", e.t. or if missing, use "unknown"
    "rounding": 0.00,  -- If rounding is not specified on the receipt, use 0.0
    "tax": 0.00,  -- If tax is not found or mentioned, use 0.0
    "taxes_not_included_sum": 0.0 -- Represents the total amount of taxes that are not included in the final total on the receipt. This is applicable in situations where taxes are itemized separately, such as in the United States. If there are no separate taxes, set to 0.0.
    "tips": 0.00,  -- If tips is not found or mentioned, use 0.0
    "items": [
        {
            "name": string,  -- Full item name (even if it spans multiple lines)
            "quantity": 0.000,  -- Quantity of the item, default 1.0 if it wasn`t written
            "measurement_unit": string,  -- Use the format "ks", "kg", etc. If not specified, default to "ks"
            "total_price_without_discount": 0.00, -- price without any discount for a single item. Always extract this value directly from the receipt
            "unit_price": 0.00,  -- Price per unit without any discount, if available. If not, write here the same value as for total_price_without_discount. Can be negative
            "total_price_with_discount": 0.00 - -- This is the full price for a single item after considering all applicable discounts.
            "discount": 0.00,  -- If discount isn't listed, assume 0.00
            "category": string  -- Category choose fromlist:Food,Beverages,Personal Care, Beauty & Health,Household Items,Electronics & Appliances,Clothing & Accessories,Home & Furniture,Entertainment & Media,Sports & Outdoors,Car,Baby Products,Stationery,Pet Supplies,Health & Fitness Services,Travel & Transportation,Insurance & Financial Services,Utilities,Gifts & Specialty Items,Services,Other options
            "item_price_with_tax": string  -- "True"/"False". Indicating whether the item prices include tax.
        }
    ]
    "taxs_items": [
        {
            "tax_name": string -- The name of the tax or tax rate.
            "percentage": 0.00 --The tax percentage.
            "tax_from_amount": 0.00 -- The amount before tax.
            "tax": 0.00 -- The tax amount itself.
            "total": 0.00 -- The total amount including tax.
            "tax_included": string  -- "True"/"False" indicating whether taxes are included in the item prices. Set to True if there is no separate line for tax on the receipt, or if it explicitly states that taxes are included. Otherwise, set to False
        }
    ]
}

#Additional Notes:
1. If no receipt is detected: Return "Receipt not found."
2. Handle various languages (including non-Latin scripts) and keep text in the original script unless translation is explicitly required.
3. If information is missing or unclear, return "unknown" or "not available" for that field.
4. Extract the full name of each item. Some items may have names split across multiple lines; in this case, concatenate the lines until you encounter a quantity or unit of measurement (e.g., "2ks"), which marks the end of the item name.
5. Some receipts could be, for example, from McDonald`s restaurant, where in receipts under menu name could be written components of this menu. In this case you should extract only menu name.
6. The total amount may not always be the largest number; ensure the context is understood from surrounding text.
7. Tips and Charity Donations: Extract and sum tips and charity donations, storing the total under the tips field.
8. Convert datetime to the "YYYY.MM.DD HH:MM:SS" format, regardless of how they appear on the receipt (e.g., MM/DD/YY, DD-MM-YYYY).
9. Handle ambiguous data consistently. If there's ambiguity about price, quantity, or any other information, make the best effort to extract it, or return "unknown."
10. Be flexible in handling varied receipt layouts, item name formats, and currencies.
11. The unit_price/price/total_price/total_price_without_discount for an item can be negative
12. After the total amount may be information about taxes, in separate tax items. Define them in taxs_items""",
                api_name="/process_image"
            )
            print(f"API response: {result}")
            
        except Exception as api_error:
            print(f"API call error: {api_error}")
            print(f"API error type: {type(api_error)}")
            print(f"API error details: {str(api_error)}")
            raise
            
        # 결과가 튜플인 경우 두 번째 요소(JSON 문자열) 사용
        if isinstance(result, tuple) and len(result) > 1:
            result = result[1]
            
        # JSON 파싱
        try:
            parsed_data = json.loads(result)
            
            # 메타데이터 필드 제거
            metadata_fields = ['input_tokens', 'output_tokens', 'total_tokens', 'time', 'file_name']
            for field in metadata_fields:
                if field in parsed_data:
                    del parsed_data[field]
            
            # 필수 필드 확인 및 기본값 설정
            required_fields = {
                'store_name': '',
                'country': 'unknown',
                'receipt_type': 'unknown',
                'address': 'unknown',
                'datetime': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'currency': 'USD',
                'sub_total_amount': 0,
                'total_price': 0,
                'total_discount': 0,
                'all_items_price_with_tax': False,
                'payment_method': 'unknown',
                'rounding': 0,
                'tax': 0,
                'taxes_not_included_sum': 0,
                'tips': 0,
                'items': [],
                'taxs_items': []
            }
            
            # 누락된 필드에 기본값 설정
            for field, default_value in required_fields.items():
                if field not in parsed_data:
                    parsed_data[field] = default_value
            
            # 날짜 형식 변환
            if 'datetime' in parsed_data and parsed_data['datetime']:
                try:
                    # YYYY.MM.DD HH:MM:SS 형식을 datetime 객체로 변환
                    dt = datetime.strptime(parsed_data['datetime'], '%Y.%m.%d %H:%M:%S')
                    # timezone 적용
                    dt = timezone.make_aware(dt)
                    # Django 형식(YYYY-MM-DD HH:MM:SS)으로 변환
                    parsed_data['datetime'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError as e:
                    print(f"Date parsing error: {e}")
                    print(f"Original datetime: {parsed_data['datetime']}")
                    # 날짜 파싱 실패 시 현재 시간 사용
                    parsed_data['datetime'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                # datetime이 없는 경우 현재 시간 사용
                parsed_data['datetime'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Boolean 필드 처리
            parsed_data['all_items_price_with_tax'] = bool(parsed_data.get('all_items_price_with_tax', False))
            
            # items의 item_price_with_tax 필드 처리
            for item in parsed_data.get('items', []):
                item['item_price_with_tax'] = bool(item.get('item_price_with_tax', False))
            
            # taxs_items의 tax_included 필드 처리
            for tax_item in parsed_data.get('taxs_items', []):
                tax_item['tax_included'] = bool(tax_item.get('tax_included', False))
                
        except json.JSONDecodeError as json_error:
            print(f"Error parsing JSON: {result}")
            print(f"JSON error details: {json_error}")
            return {
                'store_name': '',
                'country': 'unknown',
                'receipt_type': 'unknown',
                'address': 'unknown',
                'datetime': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'currency': 'USD',
                'sub_total_amount': 0,
                'total_price': 0,
                'total_discount': 0,
                'all_items_price_with_tax': False,
                'payment_method': 'unknown',
                'rounding': 0,
                'tax': 0,
                'taxes_not_included_sum': 0,
                'tips': 0,
                'items': [],
                'taxs_items': []
            }
            
        return parsed_data
        
    except Exception as e:
        print(f"Error processing image: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error details: {str(e)}")
        return {
            'store_name': '',
            'country': 'unknown',
            'receipt_type': 'unknown',
            'address': 'unknown',
            'datetime': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'currency': 'USD',
            'sub_total_amount': 0,
            'total_price': 0,
            'total_discount': 0,
            'all_items_price_with_tax': False,
            'payment_method': 'unknown',
            'rounding': 0,
            'tax': 0,
            'taxes_not_included_sum': 0,
            'tips': 0,
            'items': [],
            'taxs_items': []
        }