<script lang="ts">
  import { onMount } from 'svelte';
  import DashboardScene from '$lib/components/DashboardScene.svelte';
  import RegionScene from '$lib/components/RegionScene.svelte';
  import {
    getComponentDetail,
    getDatasetTemplate,
    getDashboard,
    getRegionScene,
    importTemplateDataset,
    resetDataset,
    uploadDataset
  } from '$lib/api';
  import { formatDateTime, notificationSeverityForRegion, severityColor } from '$lib/display';
  import type {
    ComponentDetail,
    DashboardPayload,
    Notification,
    Region,
    ScenePayload,
    SelectableComponent
  } from '$lib/types';

  let dashboard: DashboardPayload | null = null;
  let selectedRegion: Region | null = null;
  let scene: ScenePayload | null = null;
  let selectedComponent: SelectableComponent | null = null;
  let componentDetail: ComponentDetail | null = null;
  let mode: 'dashboard' | 'region' = 'dashboard';
  let loading = true;
  let errorMessage = '';
  let uploadMessage = '';
  let panelTab: 'operations' | 'setup' = 'operations';

  onMount(() => {
    void loadDashboard();
  });

  async function loadDashboard(): Promise<void> {
    loading = true;
    errorMessage = '';
    try {
      dashboard = await getDashboard();
      selectedRegion = dashboard.regions[0] ?? null;
      if (!dashboard.dataset) {
        panelTab = 'setup';
        mode = 'dashboard';
      }
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Unable to load dashboard';
    } finally {
      loading = false;
    }
  }

  async function enterRegion(region: Region): Promise<void> {
    selectedRegion = region;
    selectedComponent = null;
    componentDetail = null;
    loading = true;
    try {
      scene = await getRegionScene(region.id);
      mode = 'region';
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Unable to load region';
    } finally {
      loading = false;
    }
  }

  async function enterSelectedRegion(): Promise<void> {
    if (selectedRegion) {
      await enterRegion(selectedRegion);
    }
  }

  async function inspectComponent(component: SelectableComponent): Promise<void> {
    selectedComponent = component;
    componentDetail = null;
    try {
      componentDetail = await getComponentDetail(component.type, component.id);
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Unable to load component';
    }
  }

  function regionNotifications(region: Region | null): Notification[] {
    if (!dashboard || !region) return [];
    return dashboard.notifications.filter((item) => item.region_id === region.id);
  }

  function sceneComponents(payload: ScenePayload): SelectableComponent[] {
    return [
      ...payload.river_sections.map((item) => ({
        type: 'river_section' as const,
        id: item.id,
        label: item.name
      })),
      ...payload.gates.map((item) => ({ type: 'gate' as const, id: item.id, label: item.name })),
      ...payload.sensors.map((item) => ({
        type: 'sensor' as const,
        id: item.id,
        label: item.name
      })),
      ...payload.reservoirs.map((item) => ({
        type: 'reservoir' as const,
        id: item.id,
        label: item.name
      })),
      ...payload.vegetation_zones.map((item) => ({
        type: 'vegetation_zone' as const,
        id: item.id,
        label: item.name
      }))
    ];
  }

  async function resetSeed(): Promise<void> {
    uploadMessage = '';
    await resetDataset();
    await loadDashboard();
    mode = 'dashboard';
    panelTab = 'operations';
    uploadMessage = 'Template dataset imported to the database';
  }

  async function importTemplate(): Promise<void> {
    uploadMessage = 'Importing bundled JSON template...';
    await importTemplateDataset();
    await loadDashboard();
    mode = 'dashboard';
    panelTab = 'operations';
    uploadMessage = 'Template data uploaded to the database';
  }

  async function downloadTemplate(): Promise<void> {
    const data = await getDatasetTemplate();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'mi-demo-dataset-template.json';
    link.click();
    URL.revokeObjectURL(url);
  }

  async function handleUpload(event: Event): Promise<void> {
    const input = event.currentTarget as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    uploadMessage = 'Uploading dataset...';
    try {
      const text = await file.text();
      await uploadDataset(JSON.parse(text));
      await loadDashboard();
      mode = 'dashboard';
      panelTab = 'operations';
      uploadMessage = `${file.name} uploaded to the database`;
    } catch (error) {
      uploadMessage = error instanceof Error ? error.message : 'Upload failed';
    } finally {
      input.value = '';
    }
  }
</script>

<svelte:head>
  <title>MI Control Panel PoC</title>
</svelte:head>

<main class="workspace">
  <section class="viewport">
    <header class="topbar">
      <div>
        <p class="eyebrow">Murrumbidgee Irrigation PoC</p>
        <h1>Control Panel</h1>
      </div>
      <div class="status-strip">
        <span class="status red">{dashboard?.summary.red_count ?? 0}</span>
        <span class="status yellow">{dashboard?.summary.yellow_count ?? 0}</span>
        <span class="status green">{dashboard?.summary.green_count ?? 0}</span>
      </div>
    </header>

    {#if loading}
      <div class="loading">Loading operational view...</div>
    {:else if errorMessage}
      <div class="loading error">{errorMessage}</div>
    {:else if dashboard && mode === 'dashboard' && dashboard.dataset}
      <DashboardScene
        regions={dashboard.regions}
        notifications={dashboard.notifications}
        selectedRegionId={selectedRegion?.id ?? null}
        onSelectRegion={(region) => (selectedRegion = region)}
        onEnterRegion={enterRegion}
      />
    {:else if dashboard && !dashboard.dataset}
      <div class="empty-state">
        <h2>No Supabase data loaded</h2>
        <p>Open Data Setup and upload JSON to populate the control panel database.</p>
      </div>
    {:else if scene}
      <RegionScene {scene} selectedComponentKey={selectedComponent ? `${selectedComponent.type}:${selectedComponent.id}` : null} onSelectComponent={inspectComponent} />
    {/if}
  </section>

  <aside class="panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">Dataset</p>
        <h2>{dashboard?.dataset?.name ?? 'No dataset'}</h2>
      </div>
      {#if mode === 'region'}
        <button class="icon-button" aria-label="Return to dashboard" on:click={() => (mode = 'dashboard')}>
          Map
        </button>
      {/if}
    </div>

    <div class="tab-list" aria-label="Panel tabs">
      <button class:active={panelTab === 'operations'} on:click={() => (panelTab = 'operations')}>
        Operations
      </button>
      <button class:active={panelTab === 'setup'} on:click={() => (panelTab = 'setup')}>Data Setup</button>
    </div>

    {#if dashboard && panelTab === 'operations'}
      <div class="summary-grid">
        <div>
          <span>Regions</span>
          <strong>{dashboard.summary.region_count}</strong>
        </div>
        <div>
          <span>Alerts</span>
          <strong>{dashboard.summary.notification_count}</strong>
        </div>
      </div>
    {/if}

    {#if panelTab === 'setup'}
      <section class="panel-section selected-region">
        <h3>Supabase Data Setup</h3>
        <p>
          Upload a JSON setup file to create SQLModel records in the configured database. With a
          Supabase Postgres DSN, these records are stored in Supabase.
        </p>
      </section>

      <section class="panel-section admin">
        <h3>JSON Import</h3>
        <label class="upload">
          <input type="file" accept="application/json" on:change={handleUpload} />
          Upload JSON
        </label>
        <button class="secondary" on:click={importTemplate}>Import Template</button>
        <button class="secondary" on:click={downloadTemplate}>Download Template</button>
        {#if uploadMessage}<p class="muted">{uploadMessage}</p>{/if}
      </section>

      <section class="panel-section">
        <h3>Current Database State</h3>
        {#if dashboard?.dataset}
          <p>{dashboard.dataset.name} is active and serving the main UI.</p>
        {:else}
          <p class="muted">No active dataset exists yet. Import JSON to populate the dashboard.</p>
        {/if}
      </section>
    {:else if mode === 'dashboard' && dashboard && dashboard.dataset}
      <section class="panel-section">
        <h3>Regions</h3>
        <div class="region-list">
          {#each dashboard.regions as region}
            {@const severity = notificationSeverityForRegion(region, dashboard.notifications)}
            <button
              class:selected={selectedRegion?.id === region.id}
              class="region-row"
              on:click={() => (selectedRegion = region)}
            >
              <span class="dot" style={`background:${severityColor[severity]}`}></span>
              <span>
                <strong>{region.name}</strong>
                <small>{region.summary}</small>
              </span>
            </button>
          {/each}
        </div>
      </section>

      {#if selectedRegion}
        <section class="panel-section selected-region">
          <h3>{selectedRegion.name}</h3>
          <p>{selectedRegion.summary}</p>
          <button class="primary" on:click={enterSelectedRegion}>Enter 3D Region</button>
        </section>
        <section class="panel-section">
          <h3>Region Notifications</h3>
          {#each regionNotifications(selectedRegion) as notification}
            <article class={`notification ${notification.severity}`}>
              <strong>{notification.title}</strong>
              <p>{notification.contents}</p>
              <small>{notification.generated_from}</small>
            </article>
          {:else}
            <p class="muted">No active notifications for this region.</p>
          {/each}
        </section>
      {/if}
    {:else if scene}
      <section class="panel-section">
        <h3>{scene.region.name}</h3>
        <p>{scene.region.summary}</p>
      </section>

      {#if componentDetail && selectedComponent}
        <section class="panel-section selected-region">
          <h3>{selectedComponent.label}</h3>
          <p class="muted">{componentDetail.component_type.replace('_', ' ')}</p>
          <dl class="metric-list">
            {#each Object.entries(componentDetail.related_metrics) as [key, value]}
              <div>
                <dt>{key.replaceAll('_', ' ')}</dt>
                <dd>{String(value ?? 'n/a')}</dd>
              </div>
            {/each}
          </dl>
        </section>
        <section class="panel-section">
          <h3>Component Notifications</h3>
          {#each componentDetail.notifications as notification}
            <article class={`notification ${notification.severity}`}>
              <strong>{notification.title}</strong>
              <p>{notification.contents}</p>
              <small>{formatDateTime(notification.predicted_for)}</small>
            </article>
          {:else}
            <p class="muted">No active component notifications.</p>
          {/each}
        </section>
      {:else}
        <section class="panel-section">
          <h3>Scene Components</h3>
          <p class="muted">Select water, gates, sensors, reservoirs, or vegetation.</p>
          <div class="component-list">
            {#each sceneComponents(scene) as component}
              <button class="component-row" on:click={() => inspectComponent(component)}>
                <span>{component.type.replace('_', ' ')}</span>
                <strong>{component.label}</strong>
              </button>
            {/each}
          </div>
        </section>
      {/if}
    {/if}

    {#if panelTab === 'operations' && dashboard?.dataset}
      <section class="panel-section admin">
        <h3>Dataset</h3>
        <button class="secondary" on:click={() => (panelTab = 'setup')}>Open Setup</button>
        <button class="secondary" on:click={resetSeed}>Reimport Template</button>
        {#if uploadMessage}<p class="muted">{uploadMessage}</p>{/if}
      </section>
    {/if}
  </aside>
</main>

<style>
  :global(body) {
    margin: 0;
    min-width: 320px;
    background: #101416;
    color: #edf3ee;
    font-family:
      Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }

  button,
  input {
    font: inherit;
  }

  .workspace {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 360px;
    min-height: 100vh;
  }

  .viewport {
    position: relative;
    overflow: hidden;
    background: #162023;
  }

  .topbar {
    position: absolute;
    z-index: 5;
    top: 0;
    left: 0;
    right: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 22px;
    pointer-events: none;
  }

  .eyebrow {
    margin: 0;
    color: #99aaa4;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0;
    text-transform: uppercase;
  }

  h1,
  h2,
  h3,
  p {
    margin-top: 0;
  }

  h1 {
    margin-bottom: 0;
    font-size: 1.6rem;
  }

  h2 {
    margin-bottom: 0;
    font-size: 1.1rem;
  }

  h3 {
    margin-bottom: 10px;
    font-size: 0.92rem;
  }

  .status-strip {
    display: flex;
    gap: 8px;
  }

  .status {
    display: grid;
    min-width: 34px;
    height: 34px;
    place-items: center;
    border-radius: 6px;
    color: #111;
    font-weight: 800;
  }

  .red {
    background: #ff5a4f;
  }

  .yellow {
    background: #f2c94c;
  }

  .green {
    background: #31c873;
  }

  .panel {
    overflow-y: auto;
    border-left: 1px solid #2a3636;
    background: #151b1d;
    padding: 18px;
  }

  .panel-header {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 16px;
  }

  .tab-list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 14px;
  }

  .tab-list button {
    min-height: 34px;
    border: 1px solid #304143;
    border-radius: 6px;
    background: #111719;
    color: #c8d7d2;
    cursor: pointer;
  }

  .tab-list button.active {
    border-color: #89c2bd;
    background: #203032;
    color: #edf3ee;
    font-weight: 800;
  }

  .summary-grid div,
  .panel-section {
    border: 1px solid #2a3636;
    border-radius: 8px;
    background: #1b2426;
  }

  .summary-grid div {
    padding: 10px;
  }

  .summary-grid span,
  .muted,
  small {
    color: #9fb1ab;
  }

  .summary-grid strong {
    display: block;
    margin-top: 4px;
    font-size: 1.35rem;
  }

  .panel-section {
    margin-bottom: 14px;
    padding: 14px;
  }

  .region-list {
    display: grid;
    gap: 8px;
  }

  .component-list {
    display: grid;
    gap: 8px;
    margin-top: 12px;
  }

  .region-row {
    display: grid;
    grid-template-columns: 12px 1fr;
    gap: 10px;
    align-items: center;
    width: 100%;
    border: 1px solid transparent;
    border-radius: 6px;
    background: #111719;
    color: inherit;
    padding: 10px;
    text-align: left;
    cursor: pointer;
  }

  .component-row {
    display: grid;
    gap: 3px;
    width: 100%;
    border: 1px solid #304143;
    border-radius: 6px;
    background: #111719;
    color: inherit;
    padding: 9px 10px;
    text-align: left;
    cursor: pointer;
  }

  .component-row span {
    color: #9fb1ab;
    font-size: 0.75rem;
    text-transform: capitalize;
  }

  .region-row.selected {
    border-color: #89c2bd;
    background: #203032;
  }

  .region-row small {
    display: block;
    margin-top: 3px;
  }

  .dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }

  .primary,
  .secondary,
  .icon-button,
  .upload {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 36px;
    border-radius: 6px;
    border: 1px solid #3b4d4e;
    cursor: pointer;
  }

  .primary {
    width: 100%;
    background: #d7f3ea;
    color: #10201d;
    font-weight: 800;
  }

  .secondary,
  .icon-button,
  .upload {
    background: #223032;
    color: #edf3ee;
    padding: 0 12px;
  }

  .upload input {
    display: none;
  }

  .notification {
    margin-bottom: 8px;
    border-left: 4px solid currentColor;
    border-radius: 6px;
    background: #12191a;
    padding: 10px;
  }

  .notification.red {
    color: #ff9b93;
  }

  .notification.yellow {
    color: #f5d56f;
  }

  .notification.green {
    color: #82dfa6;
  }

  .notification p {
    margin: 6px 0;
    color: #d7e3de;
  }

  .metric-list {
    display: grid;
    gap: 8px;
    margin: 0;
  }

  .metric-list div {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 12px;
  }

  .metric-list dt {
    color: #9fb1ab;
    text-transform: capitalize;
  }

  .metric-list dd {
    margin: 0;
    text-align: right;
  }

  .admin {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .admin h3,
  .admin p {
    flex-basis: 100%;
  }

  .loading {
    display: grid;
    height: 100vh;
    place-items: center;
    color: #c8d7d2;
  }

  .loading.error {
    color: #ffaca6;
    padding: 28px;
    text-align: center;
  }

  .empty-state {
    display: grid;
    min-height: 100vh;
    place-content: center;
    padding: 32px;
    text-align: center;
  }

  .empty-state h2 {
    margin-bottom: 8px;
    font-size: 1.4rem;
  }

  .empty-state p {
    max-width: 420px;
    color: #9fb1ab;
  }

  @media (max-width: 880px) {
    .workspace {
      grid-template-columns: 1fr;
    }

    .viewport {
      min-height: 62vh;
    }

    .panel {
      max-height: none;
      border-left: 0;
      border-top: 1px solid #2a3636;
    }
  }
</style>
