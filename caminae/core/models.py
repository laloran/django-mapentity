from django.contrib.gis.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from caminae.authent.models import StructureRelated
from caminae.maintenance.models import Intervention

# GeoDjango note:
# Django automatically creates indexes on geometry fields but it uses a
# syntax which is not compatible with PostGIS 2.0. That's why index creation
# is explicitly disbaled here (see manual index creation in custom SQL files).


class Path(StructureRelated):
    geom = models.LineStringField(srid=settings.SRID, spatial_index=False)
    geom_cadastre = models.LineStringField(null=True, srid=settings.SRID,
                                           spatial_index=False)
    date_insert = models.DateField(auto_now_add=True)
    date_update = models.DateField(auto_now=True)
    valid = models.BooleanField(db_column='troncon_valide', default=True)
    name = models.CharField(null=True, max_length=20, db_column='nom_troncon')
    comments = models.TextField(null=True, db_column='remarques')

    # Override default manager
    objects = models.GeoManager()

    # Computed values (managed at DB-level with triggers)
    length = models.IntegerField(editable=False, default=0, db_column='longueur')
    ascent = models.IntegerField(
            editable=False, default=0, db_column='denivelee_positive')
    descent = models.IntegerField(
            editable=False, default=0, db_column='denivelee_negative')
    min_elevation = models.IntegerField(
            editable=False, default=0, db_column='altitude_minimum')
    max_elevation = models.IntegerField(
            editable=False, default=0, db_column='altitude_maximum')

    class Meta:
        db_table = 'troncons'


class TopologyMixin(models.Model):
    date_insert = models.DateField(auto_now_add=True)
    date_update = models.DateField(auto_now=True)
    troncons = models.ManyToManyField(Path, through='PathAggregation')
    offset = models.IntegerField(db_column='decallage')
    deleted = models.BooleanField(db_column='supprime')

    # Override default manager
    objects = models.GeoManager()

    # Computed values (managed at DB-level with triggers)
    length = models.FloatField(editable=False, db_column='longueur')
    geom = models.LineStringField(
            editable=False, srid=settings.SRID, spatial_index=False)

    kind = models.ForeignKey('TopologyMixinKind', verbose_name=_(u"Kind"))

    interventions = models.ManyToManyField(Intervention, verbose_name=_(u"Interventions"))

    class Meta:
        db_table = 'evenements'


class TopologyMixinKind(models.Model):

    code = models.IntegerField(primary_key=True)
    kind = models.CharField(verbose_name=_(u"Topology kind"), max_length=128)

    class Meta:
        db_table = 'type_evenements'


class PathAggregation(models.Model):
    path = models.ForeignKey(Path, null=False, db_column='troncon')
    topo_object = models.ForeignKey(TopologyMixin, null=False,
                                    db_column='evenement')
    start_position = models.FloatField(db_column='pk_debut')
    end_position = models.FloatField(db_column='pk_fin')

    # Override default manager
    objects = models.GeoManager()

    class Meta:
        db_table = 'evenements_troncons'
