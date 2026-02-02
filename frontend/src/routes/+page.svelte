<script lang="ts">
	import { onMount } from 'svelte';

	interface SearchResult {
		id: string;
		type: string;
		label: string | null;
		description: string | null;
	}

	interface Stats {
		total: number;
		by_type: Record<string, number>;
	}

	let query = '';
	let results: SearchResult[] = [];
	let stats: Stats | null = null;
	let loading = false;
	let searchTimeout: ReturnType<typeof setTimeout>;

	const API_BASE = 'http://localhost:8000';

	onMount(async () => {
		const response = await fetch(`${API_BASE}/stats`);
		stats = await response.json();
	});

	async function search() {
		if (!query.trim()) {
			results = [];
			return;
		}

		loading = true;
		try {
			const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&limit=20`);
			const data = await response.json();
			results = data.results;
		} catch (error) {
			console.error('Search failed:', error);
		} finally {
			loading = false;
		}
	}

	function debounceSearch() {
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(search, 300);
	}
</script>

<div class="space-y-8">
	<!-- Search -->
	<div class="rounded-lg bg-white p-6 shadow">
		<label for="search" class="block text-sm font-medium text-gray-700">Search Wikidata</label>
		<div class="mt-2">
			<input
				id="search"
				type="text"
				bind:value={query}
				on:input={debounceSearch}
				placeholder="Search for entities..."
				class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
			/>
		</div>
	</div>

	<!-- Results -->
	{#if loading}
		<div class="text-center text-gray-500">Searching...</div>
	{:else if results.length > 0}
		<div class="rounded-lg bg-white shadow">
			<ul class="divide-y divide-gray-200">
				{#each results as result}
					<li class="px-6 py-4">
						<a href="/entity/{result.id}" class="block hover:bg-gray-50">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-sm font-medium text-blue-600">{result.id}</p>
									<p class="text-lg font-semibold text-gray-900">
										{result.label || '(no label)'}
									</p>
									<p class="text-sm text-gray-500">
										{result.description || '(no description)'}
									</p>
								</div>
								<span
									class="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800"
								>
									{result.type}
								</span>
							</div>
						</a>
					</li>
				{/each}
			</ul>
		</div>
	{:else if query}
		<div class="text-center text-gray-500">No results found</div>
	{/if}

	<!-- Stats -->
	{#if stats && !query}
		<div class="rounded-lg bg-white p-6 shadow">
			<h2 class="text-lg font-semibold text-gray-900">Database Statistics</h2>
			<dl class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
				<div class="rounded-lg bg-gray-50 p-4">
					<dt class="text-sm font-medium text-gray-500">Total Entities</dt>
					<dd class="mt-1 text-2xl font-semibold text-gray-900">
						{stats.total.toLocaleString()}
					</dd>
				</div>
				{#each Object.entries(stats.by_type) as [type, count]}
					<div class="rounded-lg bg-gray-50 p-4">
						<dt class="text-sm font-medium capitalize text-gray-500">{type}s</dt>
						<dd class="mt-1 text-2xl font-semibold text-gray-900">{count.toLocaleString()}</dd>
					</div>
				{/each}
			</dl>
		</div>
	{/if}
</div>
