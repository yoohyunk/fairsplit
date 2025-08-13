from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status
from apps.splits.models import Split, Item, SplitParticipant
from apps.splits.serializers import SplitSerializer, ItemSerializer, SplitParticipantSerializer
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

class ItemViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Item instances.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Item.objects.filter(split__user=self.request.user)
