from django.db import models


# -------------------------------------------------
# ASSET MODEL
# -------------------------------------------------

class Asset(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# -------------------------------------------------
# POWER READING MODEL (Multi Reading Type Support)
# -------------------------------------------------

class PowerReading(models.Model):

    READING_TYPE_CHOICES = [
        ("power_w", "Power (W)"),
        ("voltage", "Voltage (V)"),
        ("current_a", "Current (A)"),
        ("energy_kwh", "Energy (kWh)"),
        ("power_factor", "Power Factor"),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="readings"
    )

    reading_type = models.CharField(
        max_length=30,
        choices=READING_TYPE_CHOICES,
        db_index=True
    )

    value = models.FloatField()

    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["asset", "reading_type", "-timestamp"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.asset.name} | {self.reading_type} | {self.value}"


# -------------------------------------------------
# ANOMALY LOG MODEL
# -------------------------------------------------

class AnomalyLog(models.Model):

    SEVERITY_LEVELS = [
        (1, "Low"),
        (2, "Medium"),
        (3, "High"),
        (4, "Critical"),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="anomalies"
    )

    reading = models.ForeignKey(
        PowerReading,
        on_delete=models.CASCADE,
        related_name="anomaly_logs",
        null=True,
        blank=True
    )

    reading_type = models.CharField(
        max_length=30,
        choices=PowerReading.READING_TYPE_CHOICES,
        db_index=True
    )

    value = models.FloatField()

    severity = models.IntegerField(
        choices=SEVERITY_LEVELS,
        default=2
    )

    anomaly_score = models.FloatField(
        null=True,
        blank=True
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["asset", "reading_type", "-timestamp"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Anomaly | {self.asset.name} | {self.reading_type} | Severity {self.severity}"