from django.core.management.base import BaseCommand
from incentive.models import IncentiveRule, IncentiveType


class Command(BaseCommand):
    help = 'Configura reglas iniciales para la generación automática de incentivos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Eliminar todas las reglas existentes antes de crear nuevas'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Configurando reglas de incentivos automáticos...')
        )

        if options.get('reset', False):
            deleted_count = IncentiveRule.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(f'Se eliminaron {deleted_count} reglas existentes')
            )

        # Regla para alta demanda
        high_demand_rule, created = IncentiveRule.objects.get_or_create(
            name='Alta Demanda',
            incentive_type=IncentiveType.HIGH_DEMAND,
            defaults={
                'description': 'Incentivo para propietarios cuando hay alta demanda en la zona',
                'min_demand_count': 10,
                'max_offer_demand_ratio': 0.5,
                'base_amount': 50.0,
                'max_amount': 150.0,
                'duration_days': 7,
                'cooldown_days': 3,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Creada regla: {high_demand_rule.name}')
        else:
            self.stdout.write(f'- Regla existente: {high_demand_rule.name}')

        # Regla para baja oferta
        low_supply_rule, created = IncentiveRule.objects.get_or_create(
            name='Baja Oferta',
            incentive_type=IncentiveType.LOW_SUPPLY,
            defaults={
                'description': 'Incentivo para inquilinos cuando hay pocas opciones disponibles',
                'max_offer_count': 5,
                'min_demand_count': 5,
                'base_amount': 30.0,
                'max_amount': 100.0,
                'duration_days': 5,
                'cooldown_days': 2,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Creada regla: {low_supply_rule.name}')
        else:
            self.stdout.write(f'- Regla existente: {low_supply_rule.name}')

        # Regla para equilibrio de mercado
        market_balance_rule, created = IncentiveRule.objects.get_or_create(
            name='Equilibrio de Mercado',
            incentive_type=IncentiveType.MARKET_BALANCE,
            defaults={
                'description': 'Incentivo para mantener equilibrio en zonas estables',
                'min_offer_demand_ratio': 0.5,
                'max_offer_demand_ratio': 2.0,
                'base_amount': 25.0,
                'max_amount': 75.0,
                'duration_days': 10,
                'cooldown_days': 7,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Creada regla: {market_balance_rule.name}')
        else:
            self.stdout.write(f'- Regla existente: {market_balance_rule.name}')

        # Regla para promoción de zona
        zone_promotion_rule, created = IncentiveRule.objects.get_or_create(
            name='Promoción de Zona',
            incentive_type=IncentiveType.ZONE_PROMOTION,
            defaults={
                'description': 'Incentivo promocional para aumentar actividad en zonas específicas',
                'base_amount': 40.0,
                'max_amount': 120.0,
                'duration_days': 14,
                'cooldown_days': 10,
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Creada regla: {zone_promotion_rule.name}')
        else:
            self.stdout.write(f'- Regla existente: {zone_promotion_rule.name}')

        # Mostrar resumen
        total_rules = IncentiveRule.objects.count()
        active_rules = IncentiveRule.objects.filter(is_active=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nConfiguración completada:'
                f'\n- Total de reglas: {total_rules}'
                f'\n- Reglas activas: {active_rules}'
            )
        )

        # Mostrar detalles de las reglas
        self.stdout.write('\nReglas configuradas:')
        for rule in IncentiveRule.objects.all():
            status = '🟢 ACTIVA' if rule.is_active else '🔴 INACTIVA'
            self.stdout.write(
                f'  {status} {rule.name} - ${rule.base_amount} por {rule.duration_days} días'
            )