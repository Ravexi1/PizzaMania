from rest_framework import serializers
from .models import Contact, PipelineStage, Tag, Lead, LeadStage, Note, Task
from webapp.models import Order, OrderItem, Chat, Message, Review
from django.contrib.auth.models import User


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    size_name = serializers.CharField(source='size.name', read_only=True)
    addons_display = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'size_name', 'addons_display', 'quantity', 'price']
    
    def get_addons_display(self, obj):
        """Convert addon IDs to names"""
        data = obj.addons_info
        if not data:
            return None
        try:
            from webapp.models import Addon

            # Normalize to a flat list of strings
            if isinstance(data, (list, tuple)):
                raw_values = list(data)
            elif isinstance(data, str):
                raw_values = [part.strip() for part in data.split(',') if part.strip()]
            else:
                return data

            id_values = []
            name_values = []
            for val in raw_values:
                if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
                    id_values.append(int(val))
                else:
                    name_values.append(str(val))

            if id_values:
                addon_names = list(Addon.objects.filter(id__in=id_values).values_list('name', flat=True))
                name_values.extend(addon_names)

            return ', '.join([n for n in name_values if n]) if name_values else None
        except Exception:
            return data


class OrderDetailSerializer(serializers.ModelSerializer):
    """Detailed order for cook leads."""
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'items', 'total_price', 'delivery_price', 'courier_comment', 'status', 'created_at']


class OrderMinimalSerializer(serializers.ModelSerializer):
    """Minimal Order info for courier leads."""
    customer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'customer_phone', 'total_price', 'status', 'created_at', 'street', 'entrance', 'apartment', 'courier_comment']
    
    def get_customer_name(self, obj):
        return f"{obj.customer_first_name} {obj.customer_last_name}".strip()


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'user', 'user_profile', 'first_name', 'last_name', 'phone', 'email', 'street', 'entrance', 'apartment', 'created_at', 'updated_at']


class PipelineStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineStage
        fields = ['id', 'name', 'slug', 'order', 'is_won', 'is_lost']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class LeadSerializer(serializers.ModelSerializer):
    contact = ContactSerializer(read_only=True)
    contact_id = serializers.PrimaryKeyRelatedField(source='contact', queryset=Contact.objects.all(), write_only=True)
    stage = PipelineStageSerializer(read_only=True)
    stage_id = serializers.PrimaryKeyRelatedField(source='stage', queryset=PipelineStage.objects.all(), write_only=True, required=False)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(source='tags', queryset=Tag.objects.all(), many=True, write_only=True, required=False)
    assignee = UserMinimalSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(source='assignee', queryset=User.objects.all(), write_only=True, required=False, allow_null=True)
    related_order = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            'id', 'title', 'description', 'contact', 'contact_id', 'stage', 'stage_id', 'status', 'source',
            'assignee', 'assignee_id', 'tags', 'tag_ids', 'related_order', 'related_chat', 'related_review',
            'first_response_at', 'last_touch_at', 'is_archived', 'created_at', 'updated_at'
        ]
    
    def get_related_order(self, obj):
        if not obj.related_order:
            return None
        if obj.source == 'order_cook':
            return OrderDetailSerializer(obj.related_order).data
        else:
            return OrderMinimalSerializer(obj.related_order).data
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Hide contact for cook leads
        if instance.source == 'order_cook':
            data.pop('contact', None)
        return data

    def update(self, instance, validated_data):
        assignee = validated_data.get('assignee')
        if assignee is not None:
            # Restrict assignments by source
            if instance.source == 'order_cook' and not assignee.groups.filter(name='Cook').exists():
                raise serializers.ValidationError({'assignee': 'Assignee must be a Cook for cook leads.'})
            if instance.source == 'order_courier' and not assignee.groups.filter(name='Courier').exists():
                raise serializers.ValidationError({'assignee': 'Assignee must be a Courier for courier leads.'})
            if instance.source not in ['order_cook', 'order_courier'] and assignee.groups.filter(name__in=['Cook', 'Courier']).exists():
                raise serializers.ValidationError({'assignee': 'Cook/Courier cannot be assigned to non-order leads.'})
        return super().update(instance, validated_data)


class LeadStageSerializer(serializers.ModelSerializer):
    from_stage = PipelineStageSerializer(read_only=True)
    to_stage = PipelineStageSerializer(read_only=True)
    changed_by_username = serializers.CharField(source='changed_by.username', read_only=True)
    
    class Meta:
        model = LeadStage
        fields = ['id', 'lead', 'from_stage', 'to_stage', 'changed_by', 'changed_by_username', 'reason', 'changed_at']


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'lead', 'author', 'text', 'created_at']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'lead', 'assignee', 'title', 'due_at', 'status', 'created_at', 'updated_at']


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'text', 'is_system', 'created_at', 'sender_username', 'sender_name']

    def get_sender_username(self, obj):
        return obj.sender_user.username if obj.sender_user else None


class ChatSerializer(serializers.ModelSerializer):
    operator = UserMinimalSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    unread_for_operator = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'user_name', 'user', 'operator', 'is_active', 'created_at', 'last_message', 'last_message_at', 'unread_for_operator']

    def _last_msg(self, obj):
        if not hasattr(obj, '_last_cached'):
            obj._last_cached = obj.messages.order_by('-created_at').first()
        return obj._last_cached

    def get_last_message(self, obj):
        last = self._last_msg(obj)
        if not last:
            return None
        return last.text[:200]

    def get_last_message_at(self, obj):
        last = self._last_msg(obj)
        return last.created_at if last else None

    def get_unread_for_operator(self, obj):
        last = self._last_msg(obj)
        if not last:
            return False
        # Unread/new if last message not from operator
        if last.is_system:
            return False
        if obj.operator and last.sender_user and last.sender_user == obj.operator:
            return False
        if last.sender_user and last.sender_user.is_staff:
            return False
        return True


class ReviewSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    order_id = serializers.IntegerField(source='order.id', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product_name', 'order_id', 'name', 'rating', 'comment', 'admin_comment', 'created_at']
