from django.core.management.base import BaseCommand
from django.utils import timezone
from incentive.services import IncentiveService
from zone.models import Zone


class Command(BaseCommand):
    help = 'Genera incentivos automáticos basados en oferta y demanda'

    def add_arguments(self, parser):
        parser.add_argument(
            '--zone',
            type=str,
            help='Nombre de la zona específica para generar incentivos'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin crear incentivos reales (solo mostrar lo que se haría)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada del proceso'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Iniciando generación de incentivos - {timezone.now()}')
        )

        zone_name = options.get('zone')
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: No se crearán incentivos reales')
            )

        try:
            if zone_name:
                # Generar incentivos para una zona específica
                try:
                    zone = Zone.objects.get(name__icontains=zone_name)
                    self.stdout.write(f'Procesando zona: {zone.name}')
                    
                    if verbose:
                        conditions = IncentiveService.analyze_zone_market_conditions(zone)
                        self.stdout.write(f'Condiciones de mercado: {conditions}')
                    
                    if not dry_run:
                        incentives = IncentiveService.generate_automatic_incentives_for_zone(zone)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Se generaron {len(incentives)} incentivos para {zone.name}'
                            )
                        )
                        
                        if verbose:
                            for incentive in incentives:
                                self.stdout.write(
                                    f'  - {incentive.user.username}: ${incentive.amount} '
                                    f'({incentive.get_incentive_type_display()})'
                                )
                    else:
                        self.stdout.write('Incentivos que se generarían para esta zona')
                        
                except Zone.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'Zona "{zone_name}" no encontrada')
                    )
                    return
            else:
                # Generar incentivos para todas las zonas
                self.stdout.write('Procesando todas las zonas...')
                
                if not dry_run:
                    incentives = IncentiveService.generate_automatic_incentives()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Se generaron {len(incentives)} incentivos en total'
                        )
                    )
                    
                    if verbose:
                        # Agrupar por zona
                        zones_summary = {}
                        for incentive in incentives:
                            zone_name = incentive.zone.name
                            if zone_name not in zones_summary:
                                zones_summary[zone_name] = []
                            zones_summary[zone_name].append(incentive)
                        
                        for zone_name, zone_incentives in zones_summary.items():
                            self.stdout.write(f'\n{zone_name}: {len(zone_incentives)} incentivos')
                            for incentive in zone_incentives:
                                self.stdout.write(
                                    f'  - {incentive.user.username}: ${incentive.amount} '
                                    f'({incentive.get_incentive_type_display()})'
                                )
                else:
                    self.stdout.write('Analizando todas las zonas...')
                    
                    for zone in Zone.objects.all():
                        conditions = IncentiveService.analyze_zone_market_conditions(zone)
                        self.stdout.write(f'\n{zone.name}:')
                        self.stdout.write(f'  - Ofertas: {zone.offer_count}')
                        self.stdout.write(f'  - Demanda: {zone.demand_count}')
                        self.stdout.write(f'  - Ratio O/D: {conditions["offer_demand_ratio"]:.2f}')
                        self.stdout.write(f'  - Score actividad: {conditions["activity_score"]:.2f}')
                        
                        if conditions['high_demand']:
                            self.stdout.write('  ⚠️  Alta demanda detectada')
                        if conditions['low_supply']:
                            self.stdout.write('  ⚠️  Baja oferta detectada')
                        if conditions['low_activity']:
                            self.stdout.write('  ⚠️  Baja actividad detectada')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error durante la generación de incentivos: {e}')
            )
            raise

        self.stdout.write(
            self.style.SUCCESS(f'Proceso completado - {timezone.now()}')
        )