from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from src.Infrastructure.DjangoFramework.persistence.models import UserProfile

class SubadminCreationForm(UserCreationForm):
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'w-full bg-black/20 border border-white/20 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent'}))
    
    # New Fields
    rank = forms.ChoiceField(
        choices=[('ADMIN', 'Admin / Dueño'), ('SUBADMIN', 'Subadmin / Ayudante')],
        required=False, # Handled manually if hidden
        widget=forms.Select(attrs={'class': 'w-full bg-gray-900 border border-white/20 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent'})
    )
    
    boss = forms.ModelChoiceField(
        queryset=User.objects.none(), # Populated in init
        required=False,
        label="Jefe (Solo para Subadmins)",
        widget=forms.Select(attrs={'class': 'w-full bg-gray-900 border border-white/20 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'rank', 'boss')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Tailwind for all standard fields
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({
                    'class': 'w-full bg-black/20 border border-white/20 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-accent'
                })

        # Logic: Superuser sees options, Admin does not
        if self.user and self.user.is_superuser:
            # Populate boss queryset with Admins only
            # Need to filter users who have rank='ADMIN'
            try:
                self.fields['boss'].queryset = User.objects.filter(profile__rank='ADMIN')
            except Exception:
                pass 
        else:
            # Hide extra fields for normal Admins
            # We remove them from the form so they don't validate, 
            # OR we hide them. Removing is safer validation-wise if we handle save manually.
            if 'rank' in self.fields: del self.fields['rank']
            if 'boss' in self.fields: del self.fields['boss']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso (ignorando mayúsculas/minúsculas).")
        return username
