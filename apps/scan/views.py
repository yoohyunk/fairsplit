from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync
from .models import ReceiptImage, ReceiptItem, TaxItem
from .serializers import ReceiptImageSerializer, ReceiptItemSerializer
from .utils import parse_receipt_text
import os


# Create your views here.

class ScanViewSet(viewsets.ModelViewSet):
    queryset = ReceiptImage.objects.all()
    serializer_class = ReceiptImageSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def test_scan(self, request):
        """
        Test endpoint for scanning receipts without authentication
        """
        image_url = request.data.get('image_url')
        if not image_url:
            return Response(
                {'error': 'image_url is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 영수증 이미지 파싱
            parsed_data = parse_receipt_text(image_url)
            
            # Return parsed data without saving to database
            return Response({
                'message': 'Receipt parsed successfully',
                'parsed_data': parsed_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in test_scan view: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def scan(self, request):
        """
        영수증 이미지 URL을 받아 파싱하고 저장합니다.
        """
        image_url = request.data.get('image_url')
        if not image_url:
            return Response(
                {'error': 'image_url is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 영수증 이미지 파싱
            parsed_data = parse_receipt_text(image_url)
            
            # ReceiptImage 생성
            receipt = ReceiptImage.objects.create(
                image=image_url,
                store_name=parsed_data.get('store_name', ''),
                country=parsed_data.get('country', 'unknown'),
                receipt_type=parsed_data.get('receipt_type', 'unknown'),
                address=parsed_data.get('address', ''),
                datetime=parsed_data.get('datetime'),
                currency=parsed_data.get('currency', 'USD'),
                subtotal=parsed_data.get('sub_total_amount', 0),
                tax=parsed_data.get('tax', 0),
                total=parsed_data.get('total_price', 0),
                total_discount=parsed_data.get('total_discount', 0),
                all_items_price_with_tax=parsed_data.get('all_items_price_with_tax', False),
                payment_method=parsed_data.get('payment_method', 'unknown'),
                rounding=parsed_data.get('rounding', 0),
                taxes_not_included_sum=parsed_data.get('taxes_not_included_sum', 0),
                tips=parsed_data.get('tips', 0)
            )

            # ReceiptItem 생성
            for item_data in parsed_data.get('items', []):
                ReceiptItem.objects.create(
                    receipt=receipt,
                    name=item_data.get('name', ''),
                    quantity=item_data.get('quantity', 1),
                    measurement_unit=item_data.get('measurement_unit', 'ks'),
                    total_price_without_discount=item_data.get('total_price_without_discount', 0),
                    unit_price=item_data.get('unit_price', 0),
                    total_price_with_discount=item_data.get('total_price_with_discount', 0),
                    discount=item_data.get('discount', 0),
                    category=item_data.get('category', 'Other'),
                    item_price_with_tax=item_data.get('item_price_with_tax', False)
                )

            # TaxItem 생성
            for tax_item in parsed_data.get('taxs_items', []):
                TaxItem.objects.create(
                    receipt=receipt,
                    tax_name=tax_item.get('tax_name', ''),
                    percentage=tax_item.get('percentage', 0),
                    tax_from_amount=tax_item.get('tax_from_amount', 0),
                    tax=tax_item.get('tax', 0),
                    total=tax_item.get('total', 0),
                    tax_included=tax_item.get('tax_included', False)
                )

            return Response(ReceiptImageSerializer(receipt).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Error in scan view: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        receipt = self.get_object()
        items = ReceiptItem.objects.filter(receipt=receipt)
        serializer = ReceiptItemSerializer(items, many=True)
        return Response(serializer.data)
    
class ReceiptItemViewSet(viewsets.ModelViewSet):
    queryset = ReceiptItem.objects.all()
    serializer_class = ReceiptItemSerializer
    permission_classes = [IsAuthenticated]