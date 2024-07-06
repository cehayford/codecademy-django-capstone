from django.shortcuts import redirect
from django.db.models import Sum, F
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.db.models.functions import Coalesce
from .models import Ingredient, MenuItem, Purchase, RecipeRequirement, PotionItem
from .forms import IngredientForm, MenuItemForm, RecipeRequirementForm, PotionItemForm


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ingredients"] = Ingredient.objects.all()
        context["menu_items"] = MenuItem.objects.all()
        context["purchases"] = Purchase.objects.all()
        return context


class IngredientsView(LoginRequiredMixin, ListView):
    template_name = "inventory/ingredients_list.html"
    model = Ingredient


class NewIngredientView(LoginRequiredMixin, CreateView):
    template_name = "inventory/add_ingredient.html"
    model = Ingredient
    form_class = IngredientForm


class UpdateIngredientView(LoginRequiredMixin, UpdateView):
    template_name = "inventory/update_ingredient.html"
    model = Ingredient
    form_class = IngredientForm


class MenuView(LoginRequiredMixin, ListView):
    template_name = "inventory/menu_list.html"
    model = MenuItem


class NewMenuItemView(LoginRequiredMixin, CreateView):
    template_name = "inventory/add_menu_item.html"
    model = MenuItem
    form_class = MenuItemForm


class NewRecipeRequirementView(LoginRequiredMixin, CreateView):
    template_name = "inventory/add_recipe_requirement.html"
    model = RecipeRequirement
    form_class = RecipeRequirementForm


class PurchasesView(LoginRequiredMixin, ListView):
    template_name = "inventory/purchase_list.html"
    model = Purchase


class NewPurchaseView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/add_purchase.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["menu_items"] = [X for X in MenuItem.objects.all() if X.available()]
        return context

    def post(self, request):
        menu_item_id = request.POST["menu_item"]
        menu_item = MenuItem.objects.get(pk=menu_item_id)
        requirements = menu_item.reciperequirement_set
        purchase = Purchase(menu_item=menu_item)

        for requirement in requirements.all():
            required_ingredient = requirement.ingredient
            required_ingredient.quantity -= requirement.quantity
            required_ingredient.save()

        purchase.save()
        return redirect("/purchases")


class ReportView(LoginRequiredMixin, TemplateView):
    template_name = "magicshop/reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["purchases"] = Purchase.objects.all()
        revenue = Purchase.objects.aggregate(
            revenue=Sum("potion_item__price"))["revenue"]
        total_cost = 0
        for purchase in Purchase.objects.all():
            for recipe_requirement in purchase.potion_item.reciperequirement_set.all():
                total_cost += recipe_requirement.ingredient.price_per_unit *\
                    recipe_requirement.quantity
        total_cost = 0
        context["revenue"] = revenue
        context["total_cost"] = total_cost
        context["profit"] = revenue - total_cost
        return context



def log_out(request):
    logout(request)
    return redirect("/")


class PotionView(LoginRequiredMixin, ListView):
    template_name = "magicshop/potion_list.html"
    model = PotionItem

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_dict = {}
        
        for potion in PotionItem.objects.all():
            total_cost = 0
            for requirement in potion.reciperequirement_set.all():
                total_cost += requirement.req_cost()
            total_dict[potion.id] = {'total_cost':round(total_cost, 2), 'profit_cost':round(potion.price - total_cost, 2)}
        context["total_dict"] = total_dict
        return context

class NewPotionItemView(LoginRequiredMixin, CreateView):
    template_name = "magicshop/add_potion_item.html"
    model = PotionItem
    form_class = PotionItemForm

class UpdatePotionItemView(LoginRequiredMixin, UpdateView):
    template_name = "magicshop/update_potion_item.html"
    model = PotionItem
    form_class = PotionItemForm
    success_url = "/potions"

class DeletePotionItemView(LoginRequiredMixin, DeleteView):
    template_name = "magicshop/delete_potion_item.html"
    model = PotionItem
    form_class = PotionItemForm
    success_url = "/potions"
    