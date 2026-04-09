<script lang="ts">
	import { listDrives, listFiles, listFolder, getShareLink, type Service, type FileEntry, type ShareLink } from '$lib/api';
	import { onMount } from 'svelte';

	let services: Service[] = $state([]);
	let selectedService: string | null = $state(null);
	let columns: FileEntry[][] = $state([]);
	let selectedFile: FileEntry | null = $state(null);
	let shareLink: ShareLink | null = $state(null);
	let loading = $state(false);

	onMount(async () => {
		services = await listDrives();
	});

	async function selectService(id: string) {
		selectedService = id;
		selectedFile = null;
		shareLink = null;
		loading = true;
		const files = await listFiles(id);
		columns = [files];
		loading = false;
	}

	async function clickEntry(entry: FileEntry, columnIndex: number) {
		columns = columns.slice(0, columnIndex + 1);
		shareLink = null;

		if (entry.type === 'directory' && selectedService) {
			selectedFile = null;
			loading = true;
			const children = await listFolder(selectedService, entry.id);
			columns = [...columns, children];
			loading = false;
		} else {
			selectedFile = entry;
		}
	}

	async function share() {
		if (!selectedService || !selectedFile) return;
		shareLink = await getShareLink(selectedService, selectedFile.id);
	}

	function formatSize(bytes: number): string {
		if (bytes === 0) return '\u2014';
		const units = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			year: 'numeric', month: 'short', day: 'numeric',
			hour: '2-digit', minute: '2-digit'
		});
	}
</script>

<div class="h-screen flex flex-col bg-gray-950 text-gray-100">
	<header class="flex items-center gap-4 px-6 py-3 border-b border-gray-800 bg-gray-900">
		<h1 class="text-lg font-semibold tracking-tight">OpenBURO</h1>
		<div class="flex gap-2">
			{#each services as service}
				<button
					class="px-3 py-1.5 rounded-md text-sm transition-colors {selectedService === service.id
						? 'bg-blue-600 text-white'
						: 'bg-gray-800 text-gray-300 hover:bg-gray-700'}"
					onclick={() => selectService(service.id)}
				>
					{service.name}
				</button>
			{/each}
		</div>
	</header>

	<div class="flex flex-1 overflow-hidden">
		<div class="flex flex-1 overflow-x-auto">
			{#if columns.length === 0}
				<div class="flex items-center justify-center flex-1 text-gray-500">
					Select a service to browse files
				</div>
			{/if}

			{#each columns as column, colIdx}
				<div class="min-w-64 max-w-80 border-r border-gray-800 overflow-y-auto shrink-0">
					{#each column as entry}
						<button
							class="w-full flex items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-800 transition-colors
								{selectedFile?.id === entry.id ? 'bg-gray-800 text-white' : 'text-gray-300'}
								{entry.type === 'directory' && columns[colIdx + 1] ? 'bg-gray-800/50' : ''}"
							onclick={() => clickEntry(entry, colIdx)}
						>
							{#if entry.type === 'directory'}
								<svg class="w-4 h-4 text-blue-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
								</svg>
							{:else}
								<svg class="w-4 h-4 text-gray-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
								</svg>
							{/if}
							<span class="truncate">{entry.name}</span>
							{#if entry.type === 'directory'}
								<svg class="w-3 h-3 text-gray-600 ml-auto shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
								</svg>
							{/if}
						</button>
					{/each}
					{#if column.length === 0}
						<div class="px-3 py-4 text-sm text-gray-600">Empty folder</div>
					{/if}
				</div>
			{/each}

			{#if loading}
				<div class="flex items-center justify-center min-w-64 text-gray-500 text-sm">
					Loading...
				</div>
			{/if}
		</div>

		{#if selectedFile}
			<div class="w-80 border-l border-gray-800 bg-gray-900 p-5 overflow-y-auto shrink-0">
				<h2 class="font-medium text-base mb-4 break-words">{selectedFile.name}</h2>

				<dl class="space-y-3 text-sm">
					<div>
						<dt class="text-gray-500">Type</dt>
						<dd class="text-gray-200">{selectedFile.mime_type}</dd>
					</div>
					<div>
						<dt class="text-gray-500">Size</dt>
						<dd class="text-gray-200">{formatSize(selectedFile.size)}</dd>
					</div>
					<div>
						<dt class="text-gray-500">Path</dt>
						<dd class="text-gray-200 break-all">{selectedFile.path}</dd>
					</div>
					<div>
						<dt class="text-gray-500">Owner</dt>
						<dd class="text-gray-200">{selectedFile.owner}</dd>
					</div>
					<div>
						<dt class="text-gray-500">Modified</dt>
						<dd class="text-gray-200">{formatDate(selectedFile.last_modified)}</dd>
					</div>
					<div>
						<dt class="text-gray-500">Created</dt>
						<dd class="text-gray-200">{formatDate(selectedFile.creation_date)}</dd>
					</div>
				</dl>

				<button
					class="mt-6 w-full px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-md text-sm font-medium transition-colors"
					onclick={share}
				>
					Generate Share Link
				</button>

				{#if shareLink}
					<div class="mt-3 p-3 bg-gray-800 rounded-md">
						<p class="text-xs text-gray-400 mb-1">Share link</p>
						<a href={shareLink.url} target="_blank" class="text-sm text-blue-400 hover:underline break-all">
							{shareLink.url}
						</a>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>
