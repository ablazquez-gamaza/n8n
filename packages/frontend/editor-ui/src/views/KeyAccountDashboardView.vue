<script setup lang="ts">
import { useDocumentTitle } from '@/composables/useDocumentTitle';
import { onMounted } from 'vue';
import { N8nButton, N8nHeading, N8nText } from '@n8n/design-system';

const kpiCards = [
	{ label: 'SLA medio', value: '98.6%', trend: '+0.8% vs. mes anterior' },
	{ label: 'NPS promedio', value: '62', trend: '+4 puntos' },
	{ label: 'Tiempo medio de respuesta', value: '1h 42m', trend: '-12% semanal' },
	{ label: 'Contratos en riesgo', value: '3', trend: 'Revisión prioritaria' },
];

const clients = [
	{
		name: 'Telefónica Norte',
		segment: 'Telco',
		sla: '99.1%',
		nps: 58,
		status: 'Activo',
		nextReview: '12/11/2024',
	},
	{
		name: 'Retail Nova',
		segment: 'Retail',
		sla: '97.4%',
		nps: 63,
		status: 'En seguimiento',
		nextReview: '25/10/2024',
	},
	{
		name: 'Finanzas Atlas',
		segment: 'Banca',
		sla: '98.9%',
		nps: 69,
		status: 'Activo',
		nextReview: '03/12/2024',
	},
	{
		name: 'Energía Solaris',
		segment: 'Utilities',
		sla: '96.8%',
		nps: 52,
		status: 'Plan de mejora',
		nextReview: '18/10/2024',
	},
];

const contracts = [
	{
		client: 'Telefónica Norte',
		renewal: '31/01/2025',
		value: '€420k',
		sla: '99%',
		status: 'Renovación preparada',
	},
	{
		client: 'Retail Nova',
		renewal: '15/12/2024',
		value: '€275k',
		sla: '97%',
		status: 'Negociación',
	},
	{
		client: 'Energía Solaris',
		renewal: '05/11/2024',
		value: '€190k',
		sla: '96%',
		status: 'Alerta de servicio',
	},
];

const pliegos = [
	{
		client: 'Finanzas Atlas',
		compliance: '92%',
		nextAudit: '21/10/2024',
		owner: 'Equipo Calidad',
	},
	{
		client: 'Telefónica Norte',
		compliance: '96%',
		nextAudit: '14/11/2024',
		owner: 'Operaciones',
	},
	{
		client: 'Retail Nova',
		compliance: '88%',
		nextAudit: '09/10/2024',
		owner: 'Legal & Compliance',
	},
];

const tasks = [
	{
		title: 'Revisión SLA mensual con Telefónica Norte',
		priority: 'Alta',
		due: '08/10/2024',
		owner: 'Key Account',
		status: 'Pendiente',
	},
	{
		title: 'Actualizar pliego de condiciones Retail Nova',
		priority: 'Media',
		due: '10/10/2024',
		owner: 'Legal',
		status: 'En progreso',
	},
	{
		title: 'Preparar QBR Finanzas Atlas',
		priority: 'Alta',
		due: '17/10/2024',
		owner: 'Operaciones',
		status: 'Pendiente',
	},
	{
		title: 'Plan de mejora Energía Solaris',
		priority: 'Crítica',
		due: '05/10/2024',
		owner: 'Calidad',
		status: 'Bloqueada',
	},
];

const documentTitle = useDocumentTitle();

onMounted(() => {
	documentTitle.set('Key Account Manager | Control de clientes');
});
</script>

<template>
	<div :class="$style.page">
		<header :class="$style.header">
			<div>
				<N8nHeading size="xlarge">Control integral de cuentas</N8nHeading>
				<N8nText size="large" color="text-base">
					BBDD unificada para KPIs, SLAs, contratos, pliegos y tareas de cada cliente.
				</N8nText>
			</div>
			<div :class="$style.headerActions">
				<N8nButton type="primary" icon="plus">Nuevo cliente</N8nButton>
				<N8nButton type="secondary" icon="check">Crear tarea</N8nButton>
			</div>
		</header>

		<nav :class="$style.modules">
			<span>Dashboard</span>
			<span>Clientes</span>
			<span>Contratos</span>
			<span>Pliegos</span>
			<span>Tareas</span>
		</nav>

		<section :class="$style.section">
			<N8nHeading size="large">Dashboard</N8nHeading>
			<div :class="$style.kpiGrid">
				<div v-for="card in kpiCards" :key="card.label" :class="$style.kpiCard">
					<N8nText size="small" color="text-light">{{ card.label }}</N8nText>
					<N8nHeading size="large">{{ card.value }}</N8nHeading>
					<N8nText size="small" color="text-base">{{ card.trend }}</N8nText>
				</div>
			</div>
		</section>

		<section :class="$style.section">
			<div :class="$style.sectionHeader">
				<N8nHeading size="large">Clientes</N8nHeading>
				<N8nText size="small" color="text-base">
					Seguimiento operativo y comercial con KPIs críticos por cuenta.
				</N8nText>
			</div>
			<div :class="$style.table">
				<div :class="$style.tableRowHeader">
					<span>Cliente</span>
					<span>Segmento</span>
					<span>SLA</span>
					<span>NPS</span>
					<span>Estado</span>
					<span>Próxima revisión</span>
				</div>
				<div v-for="client in clients" :key="client.name" :class="$style.tableRow">
					<span>{{ client.name }}</span>
					<span>{{ client.segment }}</span>
					<span>{{ client.sla }}</span>
					<span>{{ client.nps }}</span>
					<span>{{ client.status }}</span>
					<span>{{ client.nextReview }}</span>
				</div>
			</div>
		</section>

		<section :class="$style.sectionGrid">
			<div :class="$style.card">
				<N8nHeading size="large">Contratos</N8nHeading>
				<N8nText size="small" color="text-base">
					Control de renovaciones, valor y situación de cada contrato.
				</N8nText>
				<div :class="$style.table">
					<div :class="$style.tableRowHeader">
						<span>Cliente</span>
						<span>Renovación</span>
						<span>Valor</span>
						<span>SLA</span>
						<span>Estado</span>
					</div>
					<div v-for="contract in contracts" :key="contract.client" :class="$style.tableRow">
						<span>{{ contract.client }}</span>
						<span>{{ contract.renewal }}</span>
						<span>{{ contract.value }}</span>
						<span>{{ contract.sla }}</span>
						<span>{{ contract.status }}</span>
					</div>
				</div>
			</div>
			<div :class="$style.card">
				<N8nHeading size="large">Pliegos</N8nHeading>
				<N8nText size="small" color="text-base">
					Indicadores de cumplimiento y auditorías próximas.
				</N8nText>
				<div :class="$style.table">
					<div :class="$style.tableRowHeader">
						<span>Cliente</span>
						<span>Cumplimiento</span>
						<span>Próxima auditoría</span>
						<span>Responsable</span>
					</div>
					<div v-for="pliego in pliegos" :key="pliego.client" :class="$style.tableRow">
						<span>{{ pliego.client }}</span>
						<span>{{ pliego.compliance }}</span>
						<span>{{ pliego.nextAudit }}</span>
						<span>{{ pliego.owner }}</span>
					</div>
				</div>
			</div>
		</section>

		<section :class="$style.section">
			<div :class="$style.sectionHeader">
				<N8nHeading size="large">Tareas y planner</N8nHeading>
				<N8nText size="small" color="text-base">
					To-do operativo para coordinar equipos de cuenta.
				</N8nText>
			</div>
			<div :class="$style.taskList">
				<div v-for="task in tasks" :key="task.title" :class="$style.taskRow">
					<div>
						<N8nText size="small" color="text-light">Prioridad {{ task.priority }}</N8nText>
						<N8nHeading size="medium">{{ task.title }}</N8nHeading>
					</div>
					<div :class="$style.taskMeta">
						<span>{{ task.owner }}</span>
						<span>{{ task.due }}</span>
						<span :class="$style.taskStatus">{{ task.status }}</span>
					</div>
				</div>
			</div>
		</section>
	</div>
</template>

<style lang="scss" module>
.page {
	padding: var(--spacing-2xl);
	display: flex;
	flex-direction: column;
	gap: var(--spacing-2xl);
	background: var(--color-background-light);
	min-height: 100%;
}

.header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: var(--spacing-xl);
	flex-wrap: wrap;
}

.headerActions {
	display: flex;
	gap: var(--spacing-s);
}

.modules {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
	gap: var(--spacing-s);

	span {
		padding: var(--spacing-s) var(--spacing-m);
		background: var(--color-background-xlight);
		border-radius: var(--border-radius-large);
		text-align: center;
		font-weight: 600;
		color: var(--color-text-base);
	}
}

.section {
	display: flex;
	flex-direction: column;
	gap: var(--spacing-m);
}

.sectionHeader {
	display: flex;
	flex-direction: column;
	gap: var(--spacing-2xs);
}

.kpiGrid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
	gap: var(--spacing-m);
}

.kpiCard {
	padding: var(--spacing-m);
	background: var(--color-background-xlight);
	border-radius: var(--border-radius-large);
	display: flex;
	flex-direction: column;
	gap: var(--spacing-2xs);
	box-shadow: var(--box-shadow-s);
}

.sectionGrid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
	gap: var(--spacing-l);
}

.card {
	background: var(--color-background-xlight);
	border-radius: var(--border-radius-large);
	padding: var(--spacing-m);
	display: flex;
	flex-direction: column;
	gap: var(--spacing-s);
	box-shadow: var(--box-shadow-s);
}

.table {
	display: grid;
	gap: var(--spacing-2xs);
}

.tableRowHeader,
.tableRow {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
	gap: var(--spacing-xs);
	padding: var(--spacing-xs) var(--spacing-s);
	border-radius: var(--border-radius-base);
}

.tableRowHeader {
	background: var(--color-background-base);
	font-weight: 600;
	color: var(--color-text-light);
	text-transform: uppercase;
	font-size: 0.75rem;
}

.tableRow {
	background: var(--color-background-base);
}

.taskList {
	display: grid;
	gap: var(--spacing-s);
}

.taskRow {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: var(--spacing-m);
	padding: var(--spacing-s) var(--spacing-m);
	background: var(--color-background-xlight);
	border-radius: var(--border-radius-large);
	box-shadow: var(--box-shadow-s);
	flex-wrap: wrap;
}

.taskMeta {
	display: flex;
	gap: var(--spacing-m);
	font-weight: 600;
	color: var(--color-text-light);
}

.taskStatus {
	padding: 2px 10px;
	border-radius: 999px;
	background: var(--color-foreground-xlight);
	color: var(--color-text-base);
}
</style>
