from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .ml_models import  asset_models
import numpy as np
from datetime import datetime
import json
import random
from .models import Asset, PowerReading, AnomalyLog
from myapp.utils.feature_engineering import build_feature_vector
from .simulator import ASSET_CONFIG, READING_TYPES, cascade_state
from .ml_models import asset_models
@login_required
def home(request):
    return render(request, 'index.html')
@login_required
def water(request):
    return render(request, 'water.html')

def electricity(request):

    assets_data = []
    cascade_risk = 0

    selected_asset_name = request.GET.get("asset")
    selected_reading_type = request.GET.get("reading_type", "power_w")

    all_assets = Asset.objects.all()
    READING_TYPES = [
    "power_w",
    "voltage",
    "current_a",
    "energy_kwh",
    "power_factor",
    ]
    if not all_assets.exists():
        return render(request, "electricity.html", {"assets": []})

    # If no asset selected → default to first
    if not selected_asset_name:
        selected_asset_name = all_assets.first().name

    # -------------------------------------------------
    # LOOP THROUGH ALL ASSETS (DYNAMIC)
    # -------------------------------------------------

    for asset_obj in all_assets:

        asset_name = asset_obj.name

        latest_reading = PowerReading.objects.filter(
            asset=asset_obj,
            reading_type=selected_reading_type
        ).order_by("-timestamp").first()

        if not latest_reading:
            continue

        value = latest_reading.value

        # Last 6 readings
        recent_readings = list(
            PowerReading.objects.filter(
                asset=asset_obj,
                reading_type=selected_reading_type
            ).order_by("-timestamp")[:6]
        )

        recent_readings.reverse()
        values_list = [r.value for r in recent_readings]

        status = "Normal"

        if len(values_list) >= 6:

            previous_value = values_list[-2]

            feature_vector = build_feature_vector(
                current_value=value,
                previous_value=previous_value,
                history_values=values_list,
                reading_type=selected_reading_type
            )

            # Nested model access
            asset_model = asset_models.get(asset_name, {}).get(selected_reading_type)

            if asset_model:
                model = asset_model["model"]
                scaler = asset_model["scaler"]

                scaled = scaler.transform(feature_vector)
                prediction = model.predict(scaled)[0]

                if prediction == -1:
                    status = "Anomaly"

                    # Avoid duplicate logs
                    if not AnomalyLog.objects.filter(
                        reading=latest_reading,
                        reading_type=selected_reading_type
                    ).exists():

                        AnomalyLog.objects.create(
                            asset=asset_obj,
                            reading=latest_reading,
                            reading_type=selected_reading_type,
                            value=value,
                            severity=2
                        )

                    # Simple cascade rule
                    if asset_name == "transformer_block_a":
                        cascade_risk = 1
                else:
                    status = "Normal"
            else:
                status = "Unknown"

        assets_data.append({
            "id": asset_name,
            "value": round(value, 2),
            "reading_type": selected_reading_type,
            "status": status,
            "updated": latest_reading.timestamp.strftime("%H:%M:%S")
        })

    # -------------------------------------------------
    # CHART SECTION
    # -------------------------------------------------

    try:
        selected_asset = Asset.objects.get(name=selected_asset_name)
    except Asset.DoesNotExist:
        raise Http404("Asset not found")

    last_24 = list(
        PowerReading.objects.filter(
            asset=selected_asset,
            reading_type=selected_reading_type
        ).order_by("-timestamp")[:24]
    )

    last_24.reverse()

    labels = []
    values = []
    anomalies = []

    for reading in last_24:
        labels.append(reading.timestamp.strftime("%H:%M:%S"))
        values.append(reading.value)

        is_anomaly = AnomalyLog.objects.filter(
            reading=reading,
            reading_type=selected_reading_type
        ).exists()

        anomalies.append(-1 if is_anomaly else 1)

    anomaly_count = anomalies.count(-1)
    risk_score = min(100, anomaly_count * 15)

    context = {
        "assets": assets_data,
        "labels": json.dumps(labels),
        "values": json.dumps(values),
        "anomalies": json.dumps(anomalies),
        "anomaly_count": anomaly_count,
        "risk_score": risk_score,
        "cascade_risk": cascade_risk,
        "selected_asset": selected_asset_name,
        "selected_reading_type": selected_reading_type,
        "reading_types": READING_TYPES,
    }

    return render(request, "electricity.html", context)
def land(request):
    return render(request, 'land.html')
def register(request):
    form = UserCreationForm()

    for field in form.visible_fields():
        field.field.widget.attrs['class'] = (
            'w-full p-3 rounded-lg bg-slate-700 text-white '
            'border border-slate-600 focus:outline-none '
            'focus:ring-2 focus:ring-blue-500'
        )

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        for field in form.visible_fields():
            field.field.widget.attrs['class'] = (
                'w-full p-3 rounded-lg bg-slate-700 text-white '
                'border border-slate-600 focus:outline-none '
                'focus:ring-2 focus:ring-blue-500'
            )

        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("home")

    return render(request, "register.html", {"form": form})

def login(request):
    form = AuthenticationForm()

    for field in form.visible_fields():
        field.field.widget.attrs['class'] = (
            'w-full p-3 rounded-lg bg-slate-700 text-white '
            'border border-slate-600 focus:outline-none '
            'focus:ring-2 focus:ring-blue-500'
        )

    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)

        for field in form.visible_fields():
            field.field.widget.attrs['class'] = (
                'w-full p-3 rounded-lg bg-slate-700 text-white '
                'border border-slate-600 focus:outline-none '
                'focus:ring-2 focus:ring-blue-500'
            )

        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect("home")
        else:
            return render(request, "login.html", {
                "form": form,
                "error": "Incorrect username or password!"
            })

    return render(request, "login.html", {"form": form})

def logout(request):
    auth_logout(request)
    return redirect("home")