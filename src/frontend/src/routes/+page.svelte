<script lang="ts">
	import { discoverDrives, listFiles, listFolder, getShareLink, getContentUrl, fetchContentBlob, type DriveHandle, type FileEntry, type ShareLink } from '$lib/api';
	import { onMount } from 'svelte';

	let drives: DriveHandle[] = $state([]);
	let selectedDrive: DriveHandle | null = $state(null);
	let columns: FileEntry[][] = $state([]);
	let selectedFile: FileEntry | null = $state(null);
	let shareLink: ShareLink | null = $state(null);
	let textContent: string | null = $state(null);
	let contentUrl: string | null = $state(null);
	let loading = $state(false);
	let discovering = $state(true);

	const IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/svg+xml', 'image/webp', 'image/bmp'];
	const VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/ogg'];
	const AUDIO_TYPES = ['audio/mpeg', 'audio/ogg', 'audio/wav', 'audio/webm', 'audio/flac'];
	const PDF_TYPES = ['application/pdf'];
	const TEXT_TYPES = [
		'text/plain', 'text/html', 'text/css', 'text/csv', 'text/xml',
		'text/markdown', 'text/x-python', 'text/x-java', 'text/x-c',
		'application/json', 'application/xml', 'application/javascript',
		'application/x-yaml', 'application/x-sh', 'application/typescript',
	];
	const TEXT_EXTENSIONS = [
		'.txt', '.md', '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.js', '.ts',
		'.py', '.java', '.c', '.cpp', '.h', '.go', '.rs', '.rb', '.php', '.sh', '.bash',
		'.toml', '.ini', '.cfg', '.conf', '.env', '.csv', '.sql', '.svelte', '.vue', '.jsx', '.tsx',
		'.dockerfile', '.gitignore', '.editorconfig', '.prettierrc', '.eslintrc',
	];

	function getViewerType(file: FileEntry): 'image' | 'video' | 'audio' | 'pdf' | 'text' | 'none' {
		const mime = file.mime_type.toLowerCase();
		if (IMAGE_TYPES.includes(mime)) return 'image';
		if (VIDEO_TYPES.includes(mime)) return 'video';
		if (AUDIO_TYPES.includes(mime)) return 'audio';
		if (PDF_TYPES.includes(mime)) return 'pdf';
		if (TEXT_TYPES.includes(mime)) return 'text';
		const name = file.name.toLowerCase();
		if (TEXT_EXTENSIONS.some(ext => name.endsWith(ext))) return 'text';
		return 'none';
	}

	onMount(async () => {
		drives = await discoverDrives();
		discovering = false;
	});

	async function selectDrive(drive: DriveHandle) {
		selectedDrive = drive;
		selectedFile = null;
		shareLink = null;
		textContent = null;
		revokeContentUrl();
		loading = true;
		const files = await listFiles(drive);
		columns = [files];
		loading = false;
	}

	async function clickEntry(entry: FileEntry, columnIndex: number) {
		columns = columns.slice(0, columnIndex + 1);
		shareLink = null;
		textContent = null;
		revokeContentUrl();

		if (entry.type === 'directory' && selectedDrive) {
			selectedFile = null;
			loading = true;
			const children = await listFolder(selectedDrive, entry.id);
			columns = [...columns, children];
			loading = false;
		} else if (selectedDrive) {
			selectedFile = entry;
			contentUrl = null;
			const viewerType = getViewerType(entry);

			try {
				if (viewerType === 'text') {
					const blobUrl = await fetchContentBlob(selectedDrive, entry.id);
					const res = await fetch(blobUrl);
					textContent = await res.text();
					URL.revokeObjectURL(blobUrl);
					contentUrl = 'text-loaded';
				} else if (selectedDrive.token) {
					contentUrl = await fetchContentBlob(selectedDrive, entry.id);
				} else {
					contentUrl = getContentUrl(selectedDrive, entry.id);
				}
			} catch {
				contentUrl = null;
			}
		}
	}

	function revokeContentUrl() {
		if (contentUrl?.startsWith('blob:')) {
			URL.revokeObjectURL(contentUrl);
		}
		contentUrl = null;
	}

	async function share() {
		if (!selectedDrive || !selectedFile) return;
		shareLink = await getShareLink(selectedDrive, selectedFile.id);
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
		{#if discovering}
			<span class="text-sm text-gray-500">Discovering services...</span>
		{:else}
			<div class="flex gap-2 overflow-x-auto">
				{#each drives as drive}
					<button
						class="px-3 py-1.5 rounded-md text-sm transition-colors whitespace-nowrap {selectedDrive?.id === drive.id
							? 'bg-blue-600 text-white'
							: 'bg-gray-800 text-gray-300 hover:bg-gray-700'}"
						onclick={() => selectDrive(drive)}
					>
						{drive.name}
					</button>
				{/each}
				{#if drives.length === 0}
					<span class="text-sm text-gray-500">No services found</span>
				{/if}
			</div>
		{/if}
	</header>

	<div class="flex flex-1 overflow-hidden">
		<div class="flex flex-1 overflow-x-auto">
			{#if columns.length === 0}
				<div class="flex items-center justify-center flex-1 text-gray-500">
					{#if drives.length > 0}
						Select a service to browse files
					{:else if !discovering}
						No services available
					{/if}
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

			{#if selectedFile && selectedDrive && contentUrl}
				{@const viewerType = getViewerType(selectedFile)}

				<div class="flex flex-col min-w-96 flex-1 border-r border-gray-800 bg-gray-900/50">
					<div class="flex-1 overflow-auto p-4">
						{#if viewerType === 'image'}
							<div class="flex items-center justify-center h-full">
								<img src={contentUrl} alt={selectedFile.name} class="max-w-full max-h-full object-contain rounded" />
							</div>
						{:else if viewerType === 'video'}
							<div class="flex items-center justify-center h-full">
								<video controls class="max-w-full max-h-full rounded">
									<source src={contentUrl} type={selectedFile.mime_type} />
									<track kind="captions" />
								</video>
							</div>
						{:else if viewerType === 'audio'}
							<div class="flex items-center justify-center h-full">
								<audio controls class="w-full max-w-md">
									<source src={contentUrl} type={selectedFile.mime_type} />
									<track kind="captions" />
								</audio>
							</div>
						{:else if viewerType === 'pdf'}
							<iframe src={contentUrl} title={selectedFile.name} class="w-full h-full rounded border border-gray-700"></iframe>
						{:else if viewerType === 'text' && textContent !== null}
							<pre class="text-sm text-gray-300 font-mono whitespace-pre-wrap break-words bg-gray-950 rounded p-4 border border-gray-800 overflow-auto h-full">{textContent}</pre>
						{:else}
							<div class="flex flex-col items-center justify-center h-full gap-3 text-gray-500">
								<svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
								</svg>
								<p class="text-sm">No preview available</p>
								<a href={contentUrl} download class="mt-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-md text-sm text-gray-300 transition-colors">
									Download file
								</a>
							</div>
						{/if}
					</div>

					<div class="border-t border-gray-800 px-4 py-3 flex items-center gap-4 text-xs text-gray-400 bg-gray-900 shrink-0">
						<span class="font-medium text-gray-200 truncate">{selectedFile.name}</span>
						<span>{selectedFile.mime_type}</span>
						<span>{formatSize(selectedFile.size)}</span>
						<span class="truncate">by {selectedFile.owner}</span>
						<span class="ml-auto">{formatDate(selectedFile.last_modified)}</span>
						<button
							class="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded text-white text-xs font-medium transition-colors"
							onclick={share}
						>
							Share
						</button>
						{#if shareLink}
							<a href={shareLink.url} target="_blank" class="text-blue-400 hover:underline truncate max-w-48">
								{shareLink.url}
							</a>
						{/if}
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
