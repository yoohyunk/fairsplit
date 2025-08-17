from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status
from apps.splits.models import Split, Item, SplitParticipant, ItemAssignment
from apps.splits.serializers import SplitSerializer, ItemSerializer, SplitParticipantSerializer, ItemAssignmentSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

# Create your views here.

def index(request):
    return HttpResponse("Hello, world!")

def hello(request):
    return HttpResponse("Hello, world! This is the hello view.")

class SplitViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Split instances.
    """
    queryset = Split.objects.all()
    serializer_class = SplitSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Set user and handle receipt and currency
        split = serializer.save(user=self.request.user)
        
        # Automatically add creator as participant
        SplitParticipant.objects.create(
            split=split,
            email=self.request.user.email,
            user=self.request.user,
            agreed=True,
            agreed_at=timezone.now()
        )
        
        # If receipt_id is provided in the request, link it to the split
        receipt_id = self.request.data.get('receipt_id')
        if receipt_id:
            try:
                from apps.scan.models import ReceiptImage
                receipt = ReceiptImage.objects.get(id=receipt_id)
                split.receipt = receipt
                split.currency = receipt.currency
                split.save()
            except ReceiptImage.DoesNotExist:
                pass

    def get_queryset(self):
        return Split.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_participants(self, request, pk=None):
        """
        스플릿에 참여자들을 추가합니다.
        """
        split = self.get_object()
        emails = request.data.get('emails', [])
        
        if not emails:
            return Response(
                {'error': 'emails field is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        added_participants = []
        errors = []
        
        for email in emails:
            if not email or not isinstance(email, str):
                continue
                
            email = email.strip().lower()
            
            # 이미 참여자인지 확인
            if SplitParticipant.objects.filter(split=split, email=email).exists():
                errors.append(f'{email} is already a participant')
                continue
            
            try:
                # User 모델에서 해당 이메일을 가진 사용자 찾기
                from apps.users.models import User
                user = User.objects.filter(email=email).first()
                
                participant = SplitParticipant.objects.create(
                    split=split,
                    email=email,
                    user=user
                )
                added_participants.append(SplitParticipantSerializer(participant).data)
                
            except Exception as e:
                errors.append(f'Failed to add {email}: {str(e)}')
        
        return Response({
            'added_participants': added_participants,
            'errors': errors,
            'message': f'Successfully added {len(added_participants)} participants'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """
        스플릿의 참여자 목록을 조회합니다.
        """
        split = self.get_object()
        participants = split.participants.all()
        serializer = SplitParticipantSerializer(participants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'])
    def remove_participant(self, request, pk=None):
        """
        스플릿에서 참여자를 제거합니다.
        """
        split = self.get_object()
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'email field is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            participant = SplitParticipant.objects.get(split=split, email=email)
            
            # 스플릿 생성자는 제거할 수 없음
            if participant.email == split.user.email:
                return Response(
                    {'error': 'Cannot remove split creator'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            participant.delete()
            return Response({'message': f'Removed {email} from split'})
            
        except SplitParticipant.DoesNotExist:
            return Response(
                {'error': f'{email} is not a participant'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def agree(self, request, pk=None):
        """
        현재 사용자가 스플릿에 동의합니다.
        """
        split = self.get_object()
        email = request.user.email
        
        try:
            participant = SplitParticipant.objects.get(split=split, email=email)
            participant.agreed = True
            participant.agreed_at = timezone.now()
            participant.save()
            
            return Response({'message': 'Agreed to split'})
            
        except SplitParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this split'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def calculate(self, request, pk=None):
        """
        스플릿의 개인별 비용을 계산합니다.
        """
        split = self.get_object()
        
        try:
            # 참여자별 비용 계산
            participant_costs = {}
            
            # 모든 참여자 초기화
            for participant in split.participants.all():
                participant_costs[participant.email] = {
                    'email': participant.email,
                    'total_cost': 0,
                    'items': [],
                    'agreed': participant.agreed
                }
            
            # 아이템 할당에 따른 비용 분배
            total_items_with_discount = 0
            total_items_without_discount = 0
            
            for assignment in split.assignments.all():
                receipt_item = assignment.receipt_item
                # 할인이 적용된 가격 사용 (total_discount는 별도 처리하지 않음)
                item_cost = float(receipt_item.total_price_with_discount)
                participant_count = assignment.participants.count()
                
                # 할인 계산을 위한 원가와 할인가 합계 추적
                total_items_with_discount += item_cost
                total_items_without_discount += float(receipt_item.total_price_without_discount)
                
                if participant_count > 0:
                    cost_per_person = item_cost / participant_count
                    
                    for participant in assignment.participants.all():
                        participant_costs[participant.email]['total_cost'] += cost_per_person
                        participant_costs[participant.email]['items'].append({
                            'item_id': receipt_item.id,
                            'item_name': receipt_item.name,
                            'cost': cost_per_person,
                            'quantity': receipt_item.quantity
                        })
            
            # 추가 할인 분배 (total_discount가 개별 아이템 할인의 합보다 클 경우만)
            if split.receipt and split.receipt.total_discount > 0:
                total_receipt_discount = float(split.receipt.total_discount)
                calculated_item_discount = total_items_without_discount - total_items_with_discount
                
                # 영수증의 total_discount가 개별 아이템 할인 합계보다 클 경우에만 추가 할인 적용
                additional_discount = total_receipt_discount - calculated_item_discount
                
                if additional_discount > 0 and total_items_with_discount > 0:
                    for email in participant_costs:
                        if participant_costs[email]['total_cost'] > 0:
                            discount_ratio = participant_costs[email]['total_cost'] / total_items_with_discount
                            discount_amount = additional_discount * discount_ratio
                            participant_costs[email]['total_cost'] -= discount_amount
                            
                            # 추가 할인을 별도 아이템으로 추가
                            participant_costs[email]['items'].append({
                                'item_id': 'additional_discount',
                                'item_name': 'Additional Discount',
                                'cost': -discount_amount,
                                'quantity': 1
                            })
            
            # 세금 분배 (전체 세금을 비용 비율에 따라 분배)
            if split.receipt and split.receipt.tax > 0:
                total_assigned_cost = sum(p['total_cost'] for p in participant_costs.values())
                total_tax = float(split.receipt.tax)
                
                if total_assigned_cost > 0:
                    for email in participant_costs:
                        tax_ratio = participant_costs[email]['total_cost'] / total_assigned_cost
                        tax_amount = total_tax * tax_ratio
                        participant_costs[email]['total_cost'] += tax_amount
                        
                        # 세금을 별도 아이템으로 추가
                        participant_costs[email]['items'].append({
                            'item_id': 'tax',
                            'item_name': 'Tax',
                            'cost': tax_amount,
                            'quantity': 1
                        })
            
            # 팁 분배 (전체 팁을 참여자 수로 균등 분배)
            if split.receipt and split.receipt.tips > 0:
                total_tips = float(split.receipt.tips)
                participant_count = split.participants.count()
                
                if participant_count > 0:
                    tip_per_person = total_tips / participant_count
                    
                    for email in participant_costs:
                        participant_costs[email]['total_cost'] += tip_per_person
                        participant_costs[email]['items'].append({
                            'item_id': 'tip',
                            'item_name': 'Tip',
                            'cost': tip_per_person,
                            'quantity': 1
                        })
            
            # 소수점 둘째 자리까지 반올림
            for email in participant_costs:
                participant_costs[email]['total_cost'] = round(participant_costs[email]['total_cost'], 2)
                for item in participant_costs[email]['items']:
                    item['cost'] = round(item['cost'], 2)
            
            # 전체 요약 정보
            summary = {
                'split_id': split.id,
                'split_name': split.name,
                'currency': split.currency,
                'total_amount': float(split.receipt.total) if split.receipt else 0,
                'total_discount': float(split.receipt.total_discount) if split.receipt else 0,
                'total_tax': float(split.receipt.tax) if split.receipt else 0,
                'total_tips': float(split.receipt.tips) if split.receipt else 0,
                'participant_count': split.participants.count(),
                'agreed_count': split.participants.filter(agreed=True).count()
            }
            
            return Response({
                'summary': summary,
                'participant_costs': list(participant_costs.values())
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to calculate split: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        """
        스플릿을 최종 확정합니다.
        """
        split = self.get_object()
        
        # 모든 참여자가 동의했는지 확인
        total_participants = split.participants.count()
        agreed_participants = split.participants.filter(agreed=True).count()
        
        if agreed_participants < total_participants:
            return Response(
                {'error': f'Not all participants have agreed. {agreed_participants}/{total_participants} agreed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 스플릿 상태를 finalized로 변경하고 확정 시간 설정
        split.status = 'finalized'
        split.finalization_date = timezone.now()
        split.save()
        
        return Response({
            'message': 'Split finalized successfully',
            'split_id': split.id,
            'status': split.status,
            'finalization_date': split.finalization_date
        })

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        스플릿의 요약 정보를 조회합니다.
        """
        split = self.get_object()
        
        try:
            # 기본 정보
            summary_data = {
                'id': split.id,
                'name': split.name,
                'description': split.description,
                'status': split.status,
                'currency': split.currency,
                'date_created': split.date_created,
                'participant_count': split.participants.count(),
                'agreed_count': split.participants.filter(agreed=True).count(),
                'assignment_count': split.assignments.count()
            }
            
            # 영수증 정보가 있는 경우
            if split.receipt:
                summary_data.update({
                    'receipt_id': split.receipt.id,
                    'store_name': split.receipt.store_name,
                    'total_amount': float(split.receipt.total),
                    'total_discount': float(split.receipt.total_discount),
                    'total_tax': float(split.receipt.tax),
                    'total_tips': float(split.receipt.tips)
                })
            
            return Response(summary_data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get split summary: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def receipt_items(self, request, pk=None):
        """
        스플릿에 연결된 영수증의 아이템들을 조회합니다.
        """
        split = self.get_object()
        
        if not split.receipt:
            return Response(
                {'error': 'No receipt linked to this split'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            from apps.scan.models import ReceiptItem
            items = ReceiptItem.objects.filter(receipt=split.receipt)
            
            # 할당 정보와 함께 반환
            items_data = []
            for item in items:
                item_data = {
                    'id': item.id,
                    'name': item.name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'total_price_with_discount': item.total_price_with_discount,
                    'total_price_without_discount': item.total_price_without_discount,
                    'category': item.category,
                    'assigned_participants': []
                }
                
                # 할당된 참여자들 확인
                assignment = ItemAssignment.objects.filter(
                    split=split,
                    receipt_item=item
                ).first()
                
                if assignment:
                    item_data['assigned_participants'] = [
                        p.email for p in assignment.participants.all()
                    ]
                
                items_data.append(item_data)
            
            return Response({
                'receipt_id': split.receipt.id,
                'store_name': split.receipt.store_name,
                'total': split.receipt.total,
                'currency': split.receipt.currency,
                'items': items_data
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch receipt items: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def assign_items(self, request, pk=None):
        """
        아이템들을 참여자들에게 할당합니다.
        """
        split = self.get_object()
        assignments_data = request.data.get('assignments', [])
        
        if not assignments_data:
            return Response(
                {'error': 'assignments field is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_assignments = []
        errors = []
        
        for assignment_data in assignments_data:
            receipt_item_id = assignment_data.get('receipt_item_id')
            participant_emails = assignment_data.get('participant_emails', [])
            
            if not receipt_item_id or not participant_emails:
                errors.append('receipt_item_id and participant_emails are required')
                continue
            
            try:
                # ReceiptItem 확인
                from apps.scan.models import ReceiptItem
                receipt_item = ReceiptItem.objects.get(id=receipt_item_id)
                
                # 기존 할당이 있으면 업데이트, 없으면 생성
                assignment, created = ItemAssignment.objects.get_or_create(
                    split=split,
                    receipt_item=receipt_item
                )
                
                # 참여자들 추가
                participants = SplitParticipant.objects.filter(
                    split=split,
                    email__in=participant_emails
                )
                
                if not participants.exists():
                    errors.append(f'No valid participants found for item {receipt_item.name}')
                    continue
                
                assignment.participants.set(participants)
                assignment.save()
                
                created_assignments.append(ItemAssignmentSerializer(assignment).data)
                
            except ReceiptItem.DoesNotExist:
                errors.append(f'ReceiptItem {receipt_item_id} not found')
            except Exception as e:
                errors.append(f'Failed to assign item {receipt_item_id}: {str(e)}')
        
        return Response({
            'assignments': created_assignments,
            'errors': errors,
            'message': f'Successfully created/updated {len(created_assignments)} assignments'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """
        스플릿의 아이템 할당 정보를 조회합니다.
        """
        split = self.get_object()
        assignments = split.assignments.all()
        serializer = ItemAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def update_assignment(self, request, pk=None):
        """
        특정 아이템의 할당을 업데이트합니다.
        """
        split = self.get_object()
        receipt_item_id = request.data.get('receipt_item_id')
        participant_emails = request.data.get('participant_emails', [])
        
        if not receipt_item_id:
            return Response(
                {'error': 'receipt_item_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assignment = ItemAssignment.objects.get(
                split=split,
                receipt_item_id=receipt_item_id
            )
            
            # 참여자들 업데이트
            participants = SplitParticipant.objects.filter(
                split=split,
                email__in=participant_emails
            )
            
            assignment.participants.set(participants)
            assignment.save()
            
            return Response(ItemAssignmentSerializer(assignment).data)
            
        except ItemAssignment.DoesNotExist:
            return Response(
                {'error': 'Assignment not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class ItemViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Item instances.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Item.objects.filter(split__user=self.request.user)
