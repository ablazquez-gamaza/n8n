<script setup lang="ts">
import { useDocumentTitle } from '@/composables/useDocumentTitle';
import { computed, onMounted, ref } from 'vue';
import { N8nButton, N8nHeading, N8nInput, N8nInputLabel, N8nText } from '@n8n/design-system';

type KpiCard = {
	id: number;
	label: string;
	value: string;
	trend: string;
};

type ClientRow = {
	id: number;
	name: string;
	segment: string;
	sla: string;
	nps: string;
	status: string;
	nextReview: string;
};

type ContractRow = {
	id: number;
	client: string;
	renewal: string;
	value: string;
	sla: string;
	status: string;
};

type PliegoRow = {
	id: number;
	client: string;
	compliance: string;
	nextAudit: string;
	owner: string;
};

type TaskRow = {
	id: number;
	title: string;
	priority: string;
	due: string;
	owner: string;
	status: string;
};

type SharePointConfig = {
	siteUrl: string;
	lists: {
		clients: string;
		contracts: string;
		pliegos: string;
		tasks: string;
		kpis: string;
	};
};

const DEFAULT_CONFIG: SharePointConfig = {
	siteUrl: 'https://cpgservinform.sharepoint.com/sites/PlandeAccinSAE',
	lists: {
		clients: 'Clientes',
		contracts: 'Contratos',
		pliegos: 'Pliegos',
		tasks: 'Tareas',
		kpis: 'KPIs',
	},
};

const CONFIG_KEY = 'kam.sharepoint.config';
const TOKEN_KEY = 'kam.sharepoint.token';

const config = ref<SharePointConfig>({ ...DEFAULT_CONFIG });
const accessToken = ref('');
const isLoading = ref(false);
const errorMessage = ref('');
const lastSync = ref<string | null>(null);

const kpiCards = ref<KpiCard[]>([]);
const clients = ref<ClientRow[]>([]);
const contracts = ref<ContractRow[]>([]);
const pliegos = ref<PliegoRow[]>([]);
const tasks = ref<TaskRow[]>([]);

const newClientName = ref('');
const newTaskTitle = ref('');

const hasToken = computed(() => accessToken.value.trim().length > 0);

const documentTitle = useDocumentTitle();

const getField = (item: Record<string, string>, fields: string[], fallback = ''): string => {
	for (const field of fields) {
		const value = item[field];
		if (value !== undefined && value !== null && value !== '') {
			return String(value);
		}
	}
	return fallback;
};

const normalizeDate = (value: string) => {
	if (!value) {
		return '';
	}

	try {
		return new Date(value).toLocaleDateString('es-ES');
	} catch (error) {
		return value;
	}
};

const getListEndpoint = (listName: string) =>
	`${config.value.siteUrl}/_api/web/lists/getbytitle('${encodeURIComponent(listName)}')/items`;

const getHeaders = () => ({
	Accept: 'application/json;odata=nometadata',
	Authorization: `Bearer ${accessToken.value}`,
});

const getRequestDigest = async () => {
	const response = await fetch(`${config.value.siteUrl}/_api/contextinfo`, {
		method: 'POST',
		headers: {
			...getHeaders(),
			'Content-Type': 'application/json;odata=nometadata',
		},
	});

	if (!response.ok) {
		throw new Error('No se pudo obtener el digest de SharePoint.');
	}

	const data = await response.json();
	return data.FormDigestValue as string;
};

const fetchListItems = async (listName: string) => {
	const response = await fetch(getListEndpoint(listName), {
		headers: getHeaders(),
	});

	if (!response.ok) {
		throw new Error(`No se pudo leer la lista "${listName}".`);
	}

	const data = await response.json();
	return data.value ?? [];
};

const createListItem = async (listName: string, payload: Record<string, string>) => {
	const digest = await getRequestDigest();
	const response = await fetch(getListEndpoint(listName), {
		method: 'POST',
		headers: {
			...getHeaders(),
			'Content-Type': 'application/json;odata=nometadata',
			'X-RequestDigest': digest,
		},
		body: JSON.stringify(payload),
	});

	if (!response.ok) {
		throw new Error(`No se pudo crear el registro en "${listName}".`);
	}
};

const loadData = async () => {
	if (!hasToken.value) {
		errorMessage.value = 'Introduce un token de acceso válido de SharePoint.';
		return;
	}

	isLoading.value = true;
	errorMessage.value = '';

	try {
		const [kpiItems, clientItems, contractItems, pliegoItems, taskItems] = await Promise.all([
			fetchListItems(config.value.lists.kpis),
			fetchListItems(config.value.lists.clients),
			fetchListItems(config.value.lists.contracts),
			fetchListItems(config.value.lists.pliegos),
			fetchListItems(config.value.lists.tasks),
		]);

		kpiCards.value = kpiItems.map((item: Record<string, string>) => ({
			id: item.Id,
			label: getField(item, ['Title', 'KPI', 'Indicador']),
			value: getField(item, ['Value', 'Valor']),
			trend: getField(item, ['Trend', 'Tendencia']),
		}));

		clients.value = clientItems.map((item: Record<string, string>) => ({
			id: item.Id,
			name: getField(item, ['Title', 'Cliente', 'Name']),
			segment: getField(item, ['Segment', 'Segmento']),
			sla: getField(item, ['SLA', 'Sla']),
			nps: getField(item, ['NPS', 'Nps']),
			status: getField(item, ['Status', 'Estado']),
			nextReview: normalizeDate(
				getField(item, ['NextReview', 'ProximaRevision', 'ProximaRevisión']),
			),
		}));

		contracts.value = contractItems.map((item: Record<string, string>) => ({
			id: item.Id,
			client: getField(item, ['Client', 'Cliente', 'Title']),
			renewal: normalizeDate(getField(item, ['Renewal', 'Renovacion', 'Renovación'])),
			value: getField(item, ['Value', 'Valor']),
			sla: getField(item, ['SLA', 'Sla']),
			status: getField(item, ['Status', 'Estado']),
		}));

		pliegos.value = pliegoItems.map((item: Record<string, string>) => ({
			id: item.Id,
			client: getField(item, ['Client', 'Cliente', 'Title']),
			compliance: getField(item, ['Compliance', 'Cumplimiento']),
			nextAudit: normalizeDate(
				getField(item, ['NextAudit', 'ProximaAuditoria', 'PróximaAuditoría']),
			),
			owner: getField(item, ['Owner', 'Responsable']),
		}));

		tasks.value = taskItems.map((item: Record<string, string>) => ({
			id: item.Id,
			title: getField(item, ['Title', 'Tarea']),
			priority: getField(item, ['Priority', 'Prioridad']),
			due: normalizeDate(getField(item, ['Due', 'Vencimiento', 'FechaLimite'])),
			owner: getField(item, ['Owner', 'Responsable']),
			status: getField(item, ['Status', 'Estado']),
		}));

		lastSync.value = new Date().toLocaleString('es-ES');
	} catch (error) {
		errorMessage.value =
			error instanceof Error ? error.message : 'No se pudo cargar la información de SharePoint.';
	} finally {
		isLoading.value = false;
	}
};

const saveConfig = () => {
	localStorage.setItem(CONFIG_KEY, JSON.stringify(config.value));
	localStorage.setItem(TOKEN_KEY, accessToken.value);
	void loadData();
};

const createClient = async () => {
	if (!newClientName.value) {
		return;
	}

	try {
		await createListItem(config.value.lists.clients, {
			Title: newClientName.value,
		});
		newClientName.value = '';
		void loadData();
	} catch (error) {
		errorMessage.value =
			error instanceof Error ? error.message : 'No se pudo crear el cliente en SharePoint.';
	}
};

const createTask = async () => {
	if (!newTaskTitle.value) {
		return;
	}

	try {
		await createListItem(config.value.lists.tasks, {
			Title: newTaskTitle.value,
		});
		newTaskTitle.value = '';
		void loadData();
	} catch (error) {
		errorMessage.value =
			error instanceof Error ? error.message : 'No se pudo crear la tarea en SharePoint.';
	}
};

onMounted(() => {
	documentTitle.set('Key Account Manager | Control de clientes');
	const savedConfig = localStorage.getItem(CONFIG_KEY);
	const savedToken = localStorage.getItem(TOKEN_KEY);
	if (savedConfig) {
		config.value = { ...config.value, ...JSON.parse(savedConfig) };
	}
	if (savedToken) {
		accessToken.value = savedToken;
	}
	if (savedToken) {
		void loadData();
	}
});
</script>

<template>
	<div :class="$style.page">
		<header :class="$style.header">
			<div>
				<N8nHeading size="xlarge">Control integral de cuentas</N8nHeading>
				<N8nText size="large" color="text-base">
					BBDD unificada con SharePoint para KPIs, SLAs, contratos, pliegos y tareas por cliente.
				</N8nText>
			</div>
			<div :class="$style.headerActions">
				<N8nButton type="primary" icon="refresh" :disabled="isLoading" @click="loadData">
					Actualizar datos
				</N8nButton>
				<N8nButton
					type="secondary"
					icon="check"
					:disabled="!hasToken || !newTaskTitle"
					@click="createTask"
				>
					Crear tarea
				</N8nButton>
			</div>
		</header>

		<section :class="$style.section">
			<N8nHeading size="large">Conexión SharePoint</N8nHeading>
			<N8nText size="small" color="text-base">
				Configura la URL del sitio y el token de acceso. Los datos se guardan en tu navegador para
				acceso rápido.
			</N8nText>
			<div :class="$style.configGrid">
				<N8nInputLabel label="URL del sitio" color="text-dark">
					<N8nInput v-model="config.siteUrl" type="text" placeholder="https://..." />
				</N8nInputLabel>
				<N8nInputLabel label="Token de acceso (Bearer)" color="text-dark">
					<N8nInput v-model="accessToken" type="password" placeholder="Introduce el token" />
				</N8nInputLabel>
				<N8nInputLabel label="Lista KPI" color="text-dark">
					<N8nInput v-model="config.lists.kpis" type="text" />
				</N8nInputLabel>
				<N8nInputLabel label="Lista Clientes" color="text-dark">
					<N8nInput v-model="config.lists.clients" type="text" />
				</N8nInputLabel>
				<N8nInputLabel label="Lista Contratos" color="text-dark">
					<N8nInput v-model="config.lists.contracts" type="text" />
				</N8nInputLabel>
				<N8nInputLabel label="Lista Pliegos" color="text-dark">
					<N8nInput v-model="config.lists.pliegos" type="text" />
				</N8nInputLabel>
				<N8nInputLabel label="Lista Tareas" color="text-dark">
					<N8nInput v-model="config.lists.tasks" type="text" />
				</N8nInputLabel>
			</div>
			<div :class="$style.configActions">
				<N8nButton type="primary" icon="save" @click="saveConfig">Guardar configuración</N8nButton>
				<N8nText v-if="lastSync" size="small" color="text-light">
					Última sincronización: {{ lastSync }}
				</N8nText>
			</div>
			<N8nText size="small" color="text-light">
				Listas esperadas (columnas mínimas): KPI (Title, Value, Trend), Clientes (Title, Segmento,
				SLA, NPS, Estado, PróximaRevisión), Contratos (Cliente/Title, Renovación, Valor, SLA,
				Estado), Pliegos (Cliente/Title, Cumplimiento, PróximaAuditoría, Responsable), Tareas
				(Title, Prioridad, FechaLimite/Vencimiento, Responsable, Estado).
			</N8nText>
			<N8nText v-if="errorMessage" size="small" color="danger">
				{{ errorMessage }}
			</N8nText>
		</section>

		<nav :class="$style.modules">
			<span>Dashboard</span>
			<span>Clientes</span>
			<span>Contratos</span>
			<span>Pliegos</span>
			<span>Tareas</span>
		</nav>

		<section :class="$style.section">
			<N8nHeading size="large">Dashboard</N8nHeading>
			<N8nText v-if="isLoading" size="small" color="text-light">Cargando KPIs...</N8nText>
			<div :class="$style.kpiGrid">
				<div v-for="card in kpiCards" :key="card.id" :class="$style.kpiCard">
					<N8nText size="small" color="text-light">{{ card.label }}</N8nText>
					<N8nHeading size="large">{{ card.value }}</N8nHeading>
					<N8nText size="small" color="text-base">{{ card.trend }}</N8nText>
				</div>
				<N8nText v-if="!isLoading && kpiCards.length === 0" size="small" color="text-light">
					No hay KPIs cargados en la lista seleccionada.
				</N8nText>
			</div>
		</section>

		<section :class="$style.section">
			<div :class="$style.sectionHeader">
				<N8nHeading size="large">Clientes</N8nHeading>
				<N8nText size="small" color="text-base">
					Seguimiento operativo y comercial con KPIs críticos por cuenta.
				</N8nText>
				<div :class="$style.inlineForm">
					<N8nInput
						v-model="newClientName"
						placeholder="Nuevo cliente (Title)"
						:disabled="!hasToken"
					/>
					<N8nButton
						type="secondary"
						icon="plus"
						:disabled="!newClientName || !hasToken"
						@click="createClient"
					>
						Añadir
					</N8nButton>
				</div>
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
				<div v-for="client in clients" :key="client.id" :class="$style.tableRow">
					<span>{{ client.name }}</span>
					<span>{{ client.segment }}</span>
					<span>{{ client.sla }}</span>
					<span>{{ client.nps }}</span>
					<span>{{ client.status }}</span>
					<span>{{ client.nextReview }}</span>
				</div>
				<N8nText v-if="!isLoading && clients.length === 0" size="small" color="text-light">
					No hay clientes cargados.
				</N8nText>
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
					<div v-for="contract in contracts" :key="contract.id" :class="$style.tableRow">
						<span>{{ contract.client }}</span>
						<span>{{ contract.renewal }}</span>
						<span>{{ contract.value }}</span>
						<span>{{ contract.sla }}</span>
						<span>{{ contract.status }}</span>
					</div>
					<N8nText v-if="!isLoading && contracts.length === 0" size="small" color="text-light">
						No hay contratos cargados.
					</N8nText>
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
					<div v-for="pliego in pliegos" :key="pliego.id" :class="$style.tableRow">
						<span>{{ pliego.client }}</span>
						<span>{{ pliego.compliance }}</span>
						<span>{{ pliego.nextAudit }}</span>
						<span>{{ pliego.owner }}</span>
					</div>
					<N8nText v-if="!isLoading && pliegos.length === 0" size="small" color="text-light">
						No hay pliegos cargados.
					</N8nText>
				</div>
			</div>
		</section>

		<section :class="$style.section">
			<div :class="$style.sectionHeader">
				<N8nHeading size="large">Tareas y planner</N8nHeading>
				<N8nText size="small" color="text-base">
					To-do operativo para coordinar equipos de cuenta.
				</N8nText>
				<div :class="$style.inlineForm">
					<N8nInput
						v-model="newTaskTitle"
						placeholder="Nueva tarea (Title)"
						:disabled="!hasToken"
					/>
					<N8nButton type="secondary" icon="plus" :disabled="!newTaskTitle" @click="createTask">
						Añadir
					</N8nButton>
				</div>
			</div>
			<div :class="$style.taskList">
				<div v-for="task in tasks" :key="task.id" :class="$style.taskRow">
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
				<N8nText v-if="!isLoading && tasks.length === 0" size="small" color="text-light">
					No hay tareas cargadas.
				</N8nText>
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

.configGrid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
	gap: var(--spacing-s);
	background: var(--color-background-xlight);
	padding: var(--spacing-m);
	border-radius: var(--border-radius-large);
	box-shadow: var(--box-shadow-s);
}

.configActions {
	display: flex;
	align-items: center;
	gap: var(--spacing-s);
	margin-top: var(--spacing-s);
}

.inlineForm {
	display: flex;
	gap: var(--spacing-s);
	align-items: center;
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
