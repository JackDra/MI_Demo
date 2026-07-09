<script lang="ts">
  import { goto, invalidateAll, preloadData } from '$app/navigation';
  import DashboardScene from '$lib/components/DashboardScene.svelte';
  import RegionScene from '$lib/components/RegionScene.svelte';
  import { getComponentDetail, uploadDataset } from '$lib/api';
  import { formatDateTime, severityColor, severityRank } from '$lib/display';
  import { placePath } from '$lib/placeSlugs';
  import type {
    ComponentDetail,
    DashboardLocation,
    DashboardPayload,
    Notification,
    Region,
    ScenePayload,
    SelectableComponent
  } from '$lib/types';

  export let data: {
    dashboard: DashboardPayload;
    scene?: ScenePayload;
    selectedLocation?: DashboardLocation;
    componentDetail?: ComponentDetail;
  };

  let dashboard: DashboardPayload | null = data.dashboard;
  let selectedRegion: Region | null = null;
  let selectedLocation: DashboardLocation | null = null;
  let scene: ScenePayload | null = data.scene ?? null;
  let selectedComponent: SelectableComponent | null = null;
  let componentDetail: ComponentDetail | null = data.componentDetail ?? null;
  let mode: 'dashboard' | 'region' = data.scene ? 'region' : 'dashboard';
  let loading = false;
  let errorMessage = '';
  let uploadMessage = '';
  let panelTab: 'operations' | 'notifications' | 'setup' = 'operations';
  let activeData = data;
  let panelWidth = 360;
  let isResizingPanel = false;
  let hoveredNotification: Notification | null = null;
  let hoveredLocation: DashboardLocation | null = null;

  const minPanelWidth = 320;
  const maxPanelWidth = 640;
  const minViewportWidth = 560;

  $: if (data !== activeData) {
    applyRouteData(data);
  }

  applyRouteData(data);

  function applyRouteData(nextData: typeof data): void {
    activeData = nextData;
    dashboard = nextData.dashboard;
    scene = nextData.scene ?? null;
    selectedLocation =
      nextData.selectedLocation ?? dashboard.locations[0] ?? null;
    selectedRegion =
      scene?.region ??
      (selectedLocation ? regionForLocation(selectedLocation) : null);
    selectedComponent = selectedLocation
      ? {
          type: selectedLocation.type,
          id: selectedLocation.id,
          label: selectedLocation.label
        }
      : null;
    componentDetail = nextData.componentDetail ?? null;
    mode = scene ? 'region' : 'dashboard';
    panelTab = dashboard.dataset ? 'operations' : 'setup';
    hoveredNotification = null;
    hoveredLocation = null;
    errorMessage = '';
    loading = false;
  }

  function locationKey(location: DashboardLocation | null): string | null {
    return location ? `${location.type}:${location.id}` : null;
  }

  function notificationLocationKey(
    notification: Notification | null
  ): string | null {
    if (!notification?.source_entity_id || !dashboard) return null;
    const sourceKey = `${notification.source_entity_type}:${notification.source_entity_id}`;
    return dashboard.locations.some(
      (location) => locationKey(location) === sourceKey
    )
      ? sourceKey
      : null;
  }

  function regionForLocation(location: DashboardLocation): Region | null {
    if (!dashboard) return null;
    return (
      dashboard.regions.find((region) => region.id === location.region_id) ??
      null
    );
  }

  function selectLocation(location: DashboardLocation): void {
    selectedLocation = location;
    selectedRegion = regionForLocation(location);
    selectedComponent = {
      type: location.type,
      id: location.id,
      label: location.label
    };
    componentDetail = null;
    panelTab = 'operations';
  }

  function hoverLocation(location: DashboardLocation): void {
    hoveredLocation = location;
  }

  function previewLocation(location: DashboardLocation): void {
    hoverLocation(location);
    prefetchLocation(location);
  }

  function clearHoveredLocation(): void {
    hoveredLocation = null;
  }

  function locationPath(location: DashboardLocation): string {
    return placePath(location);
  }

  function componentPath(component: SelectableComponent): string | null {
    if (component.type !== 'reservoir' && component.type !== 'river_section') {
      return null;
    }

    return placePath({
      type: component.type,
      id: component.id,
      label: component.label
    });
  }

  function prefetchLocation(location: DashboardLocation): void {
    void preloadData(locationPath(location));
  }

  async function enterLocation(location: DashboardLocation): Promise<void> {
    const href = locationPath(location);
    await preloadData(href);
    await goto(href);
  }

  async function enterSelectedRegion(): Promise<void> {
    if (selectedLocation) {
      await enterLocation(selectedLocation);
    }
  }

  function locationTypeLabel(
    type: DashboardLocation['type'] | SelectableComponent['type']
  ): string {
    return type === 'reservoir'
      ? 'Reservoir'
      : type === 'river_section'
        ? 'River'
        : type.replace('_', ' ');
  }

  async function inspectComponent(
    component: SelectableComponent
  ): Promise<void> {
    const href = componentPath(component);
    if (href) {
      await preloadData(href);
      await goto(href);
      return;
    }

    selectedComponent = component;
    componentDetail = null;
    try {
      componentDetail = await getComponentDetail(component.type, component.id);
    } catch (error) {
      errorMessage =
        error instanceof Error ? error.message : 'Unable to load component';
    }
  }

  function regionNotifications(region: Region | null): Notification[] {
    if (!dashboard || !region) return [];
    return dashboard.notifications.filter(
      (item) => item.region_id === region.id
    );
  }

  function sortedNotifications(): Notification[] {
    if (!dashboard) return [];
    return [...dashboard.notifications].sort((left, right) => {
      const severityDifference =
        severityRank[right.severity] - severityRank[left.severity];
      if (severityDifference !== 0) return severityDifference;
      return (
        new Date(right.created_at).getTime() -
        new Date(left.created_at).getTime()
      );
    });
  }

  function regionName(regionId: number | null): string {
    if (!dashboard || regionId === null) return 'Network-wide';
    return (
      dashboard.regions.find((region) => region.id === regionId)?.name ??
      'Unknown region'
    );
  }

  function sourceLabel(notification: Notification): string {
    const sourceType = notification.source_entity_type.replaceAll('_', ' ');
    return notification.source_entity_id === null
      ? sourceType
      : `${sourceType} #${notification.source_entity_id}`;
  }

  function clampPanelWidth(width: number): number {
    const maxWidthForViewport = Math.max(
      minPanelWidth,
      window.innerWidth - minViewportWidth
    );
    return Math.min(
      Math.max(width, minPanelWidth),
      Math.min(maxPanelWidth, maxWidthForViewport)
    );
  }

  function resizePanel(clientX: number): void {
    panelWidth = clampPanelWidth(window.innerWidth - clientX);
  }

  function stopPanelResize(): void {
    isResizingPanel = false;
    window.removeEventListener('pointermove', handlePanelPointerMove);
    window.removeEventListener('pointerup', stopPanelResize);
    window.removeEventListener('pointercancel', stopPanelResize);
  }

  function handlePanelPointerMove(event: PointerEvent): void {
    resizePanel(event.clientX);
  }

  function startPanelResize(event: PointerEvent): void {
    if (window.innerWidth <= 880) return;
    event.preventDefault();
    isResizingPanel = true;
    resizePanel(event.clientX);
    window.addEventListener('pointermove', handlePanelPointerMove);
    window.addEventListener('pointerup', stopPanelResize);
    window.addEventListener('pointercancel', stopPanelResize);
  }

  function handlePanelResizeKeydown(event: KeyboardEvent): void {
    const step = event.shiftKey ? 48 : 16;
    if (event.key === 'ArrowLeft') {
      panelWidth = clampPanelWidth(panelWidth + step);
      event.preventDefault();
    } else if (event.key === 'ArrowRight') {
      panelWidth = clampPanelWidth(panelWidth - step);
      event.preventDefault();
    } else if (event.key === 'Home') {
      panelWidth = maxPanelWidth;
      event.preventDefault();
    } else if (event.key === 'End') {
      panelWidth = minPanelWidth;
      event.preventDefault();
    }
  }

  function sceneComponents(payload: ScenePayload): SelectableComponent[] {
    return [
      ...payload.river_sections.map((item) => ({
        type: 'river_section' as const,
        id: item.id,
        label: item.name
      })),
      ...payload.gates.map((item) => ({
        type: 'gate' as const,
        id: item.id,
        label: item.name
      })),
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

  async function handleUpload(event: Event): Promise<void> {
    const input = event.currentTarget as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    uploadMessage = 'Uploading dataset...';
    try {
      const text = await file.text();
      await uploadDataset(JSON.parse(text));
      await invalidateAll();
      await goto('/');
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

<main
  class:resizing={isResizingPanel}
  class="workspace"
  style:--panel-width={`${panelWidth}px`}
>
  <section class="viewport">
    <header class="topbar">
      <div>
        <p class="eyebrow">Murrumbidgee Irrigation PoC</p>
        <h1>Control Panel</h1>
      </div>
      <div class="status-strip">
        <span class="status red">{dashboard?.summary.red_count ?? 0}</span>
        <span class="status yellow">{dashboard?.summary.yellow_count ?? 0}</span
        >
        <span class="status green">{dashboard?.summary.green_count ?? 0}</span>
      </div>
    </header>

    {#if loading}
      <div class="loading">Loading operational view...</div>
    {:else if errorMessage}
      <div class="loading error">{errorMessage}</div>
    {:else if dashboard && mode === 'dashboard' && dashboard.dataset}
      <DashboardScene
        locations={dashboard.locations}
        selectedLocationKey={locationKey(selectedLocation)}
        focusedLocationKey={notificationLocationKey(hoveredNotification) ??
          locationKey(hoveredLocation)}
        focusedNotification={hoveredNotification}
        onSelectLocation={selectLocation}
        onEnterLocation={enterLocation}
        onHoverLocation={hoverLocation}
        onClearHoveredLocation={clearHoveredLocation}
        onPrefetchLocation={prefetchLocation}
      />
    {:else if dashboard && !dashboard.dataset}
      <div class="empty-state">
        <h2>No Supabase data loaded</h2>
        <p>
          Open Data Setup and upload JSON to populate the control panel
          database.
        </p>
      </div>
    {:else if scene}
      <RegionScene
        {scene}
        selectedComponentKey={selectedComponent
          ? `${selectedComponent.type}:${selectedComponent.id}`
          : null}
        focusLocationType={selectedLocation?.type ?? 'river_section'}
        focusLocationId={selectedLocation?.id ?? null}
        onSelectComponent={inspectComponent}
      />
    {/if}
  </section>

  <button
    class="panel-resizer"
    type="button"
    aria-label="Resize side panel"
    on:keydown={handlePanelResizeKeydown}
    on:pointerdown={startPanelResize}
  ></button>

  <aside class="panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">Dataset</p>
        <h2>{dashboard?.dataset?.name ?? 'No dataset'}</h2>
      </div>
      {#if mode === 'region'}
        <a
          class="icon-button"
          aria-label="Return to dashboard"
          href="/"
          data-sveltekit-preload-data
        >
          Map
        </a>
      {/if}
    </div>

    <div class="tab-list" aria-label="Panel tabs">
      <button
        class:active={panelTab === 'operations'}
        on:click={() => (panelTab = 'operations')}
      >
        Operations
      </button>
      <button
        class:active={panelTab === 'notifications'}
        on:click={() => (panelTab = 'notifications')}>Notifications</button
      >
      <button
        class:active={panelTab === 'setup'}
        on:click={() => (panelTab = 'setup')}>Data Setup</button
      >
    </div>

    {#if dashboard && panelTab === 'operations'}
      <div class="summary-grid">
        <div>
          <span>Locations</span>
          <strong>{dashboard.summary.location_count}</strong>
        </div>
        <div>
          <span>Alerts</span>
          <strong>{dashboard.summary.notification_count}</strong>
        </div>
      </div>
    {/if}

    {#if panelTab === 'notifications'}
      <section class="panel-section notifications-view">
        <h3>Notifications</h3>
        {#if dashboard?.dataset}
          <div
            class="notification-table"
            role="table"
            aria-label="All notifications"
          >
            <div class="notification-row notification-heading" role="row">
              <span role="columnheader">Severity</span>
              <span role="columnheader">Details</span>
              <span role="columnheader">Source</span>
              <span role="columnheader">Timing</span>
            </div>
            {#each sortedNotifications() as notification}
              <div
                class:focused={hoveredNotification?.id === notification.id}
                class="notification-row"
                role="row"
                tabindex="0"
                aria-label={`Show ${notification.title} on the map`}
                on:mouseenter={() => (hoveredNotification = notification)}
                on:mouseleave={() => (hoveredNotification = null)}
                on:focus={() => (hoveredNotification = notification)}
                on:blur={() => (hoveredNotification = null)}
              >
                <span role="cell">
                  <span class={`severity-pill ${notification.severity}`}>
                    {notification.severity}
                  </span>
                </span>
                <span role="cell">
                  <strong>{notification.title}</strong>
                  <small>{notification.contents}</small>
                  <small>{regionName(notification.region_id)}</small>
                </span>
                <span role="cell">
                  <strong>{sourceLabel(notification)}</strong>
                  <small>{notification.generated_from}</small>
                  <small>{notification.status}</small>
                </span>
                <span role="cell">
                  <strong>{formatDateTime(notification.predicted_for)}</strong>
                  <small>{notification.prediction_horizon ?? 'Current'}</small>
                  <small>{notification.prediction_method ?? 'Rule based'}</small
                  >
                </span>
              </div>
            {:else}
              <p class="muted">No active notifications.</p>
            {/each}
          </div>
        {:else}
          <p class="muted">Upload a dataset to view notifications.</p>
        {/if}
      </section>
    {:else if panelTab === 'setup'}
      <section class="panel-section selected-region">
        <h3>Supabase Data Setup</h3>
        <p>
          Upload a JSON setup file to create SQLModel records in the configured
          database. With a Supabase Postgres DSN, these records are stored in
          Supabase.
        </p>
      </section>

      <section class="panel-section admin">
        <h3>JSON Import</h3>
        <label class="upload">
          <input
            type="file"
            accept="application/json"
            on:change={handleUpload}
          />
          Upload JSON
        </label>
        {#if uploadMessage}<p class="muted">{uploadMessage}</p>{/if}
      </section>

      <section class="panel-section">
        <h3>Current Database State</h3>
        {#if dashboard?.dataset}
          <p>{dashboard.dataset.name} is active and serving the main UI.</p>
        {:else}
          <p class="muted">
            No active dataset exists yet. Import JSON to populate the dashboard.
          </p>
        {/if}
      </section>
    {:else if mode === 'dashboard' && dashboard && dashboard.dataset}
      <section class="panel-section">
        <h3>Locations</h3>
        <div class="region-list">
          {#each dashboard.locations as location}
            <a
              class:selected={locationKey(selectedLocation) ===
                locationKey(location)}
              class:focused={locationKey(hoveredLocation) ===
                locationKey(location)}
              class="region-row"
              href={locationPath(location)}
              data-sveltekit-preload-data
              on:mouseenter={() => previewLocation(location)}
              on:mouseleave={clearHoveredLocation}
              on:focus={() => previewLocation(location)}
              on:blur={clearHoveredLocation}
            >
              <span
                class="dot"
                style={`background:${severityColor[location.severity]}`}
              ></span>
              <span>
                <strong>{location.label}</strong>
                <small
                  >{locationTypeLabel(location.type)} - {location.summary}</small
                >
              </span>
            </a>
          {/each}
        </div>
      </section>

      {#if selectedLocation && selectedRegion}
        {@const selectedLocationHref = locationPath(selectedLocation)}
        <section class="panel-section selected-region">
          <h3>{selectedLocation.label}</h3>
          <p>
            {locationTypeLabel(selectedLocation.type)} in {selectedRegion.name}
          </p>
          <a
            class="primary"
            href={selectedLocationHref}
            data-sveltekit-preload-data
            on:mouseenter={() => void preloadData(selectedLocationHref)}
            on:focus={() => void preloadData(selectedLocationHref)}
            >Enter Location</a
          >
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
          <p class="muted">
            {componentDetail.component_type.replace('_', ' ')}
          </p>
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
          <p class="muted">
            Select water, gates, sensors, reservoirs, or vegetation.
          </p>
          <div class="component-list">
            {#each sceneComponents(scene) as component}
              {@const href = componentPath(component)}
              {#if href}
                <a
                  class="component-row"
                  {href}
                  data-sveltekit-preload-data
                  on:mouseenter={() => void preloadData(href)}
                  on:focus={() => void preloadData(href)}
                >
                  <span>{component.type.replace('_', ' ')}</span>
                  <strong>{component.label}</strong>
                </a>
              {:else}
                <button
                  class="component-row"
                  on:click={() => inspectComponent(component)}
                >
                  <span>{component.type.replace('_', ' ')}</span>
                  <strong>{component.label}</strong>
                </button>
              {/if}
            {/each}
          </div>
        </section>
      {/if}
    {/if}

    {#if panelTab === 'operations' && dashboard?.dataset}
      <section class="panel-section admin">
        <h3>Dataset</h3>
        <button class="secondary" on:click={() => (panelTab = 'setup')}
          >Open Setup</button
        >
        {#if uploadMessage}<p class="muted">{uploadMessage}</p>{/if}
      </section>
    {/if}
  </aside>
</main>

<style>
  :global(html) {
    height: 100%;
  }

  :global(body) {
    margin: 0;
    height: 100%;
    min-width: 320px;
    overflow: hidden;
    background: #101416;
    color: #edf3ee;
    font-family:
      Inter,
      ui-sans-serif,
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      'Segoe UI',
      sans-serif;
  }

  button,
  input,
  a {
    font: inherit;
  }

  a {
    color: inherit;
    text-decoration: none;
  }

  .workspace {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 10px minmax(
        320px,
        var(--panel-width, 360px)
      );
    height: 100dvh;
    min-height: 0;
    overflow: hidden;
  }

  .workspace.resizing {
    cursor: col-resize;
    user-select: none;
  }

  .viewport {
    position: relative;
    min-height: 0;
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

  .panel-resizer {
    position: relative;
    width: 10px;
    min-width: 10px;
    border: 0;
    border-left: 1px solid #263232;
    border-right: 1px solid #263232;
    background: #101719;
    cursor: col-resize;
    padding: 0;
  }

  .panel-resizer::before {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 2px;
    height: 46px;
    border-radius: 999px;
    background: #4e6364;
    content: '';
    transform: translate(-50%, -50%);
  }

  .panel-resizer:hover,
  .panel-resizer:focus-visible {
    background: #182326;
    outline: none;
  }

  .panel-resizer:hover::before,
  .panel-resizer:focus-visible::before,
  .workspace.resizing .panel-resizer::before {
    background: #89c2bd;
  }

  .panel {
    min-height: 0;
    overflow-y: auto;
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
    grid-template-columns: repeat(3, minmax(0, 1fr));
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
    font-size: 0.82rem;
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

  .region-row.focused {
    border-color: #d7f3ea;
    background: #172527;
    box-shadow: inset 3px 0 0 #d7f3ea;
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

  .notifications-view {
    padding: 0;
    overflow: hidden;
  }

  .notifications-view h3,
  .notifications-view > .muted {
    margin: 14px 14px 10px;
  }

  .notification-table {
    display: grid;
    min-width: 0;
  }

  .notification-row {
    display: grid;
    grid-template-columns: 72px minmax(150px, 1.4fr) minmax(92px, 0.9fr) minmax(
        92px,
        0.8fr
      );
    gap: 10px;
    align-items: start;
    border-top: 1px solid #2a3636;
    padding: 10px 14px;
    outline: none;
    transition:
      background 0.14s ease,
      box-shadow 0.14s ease;
  }

  .notification-row:not(.notification-heading) {
    cursor: crosshair;
  }

  .notification-row:not(.notification-heading):hover,
  .notification-row:not(.notification-heading).focused,
  .notification-row:not(.notification-heading):focus-visible {
    background: #1d292a;
    box-shadow: inset 3px 0 0 #d7f3ea;
  }

  .notification-heading {
    background: #111719;
    color: #9fb1ab;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
  }

  .notification-row span[role='cell'] {
    min-width: 0;
  }

  .notification-row strong,
  .notification-row small {
    display: block;
  }

  .notification-row strong {
    overflow-wrap: anywhere;
    font-size: 0.82rem;
  }

  .notification-row small {
    margin-top: 3px;
    overflow-wrap: anywhere;
    font-size: 0.74rem;
  }

  .severity-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 54px;
    min-height: 24px;
    border-radius: 999px;
    color: #111;
    font-size: 0.7rem;
    font-weight: 900;
    text-transform: uppercase;
  }

  .severity-pill.red {
    background: #ff5a4f;
  }

  .severity-pill.yellow {
    background: #f2c94c;
  }

  .severity-pill.green {
    background: #31c873;
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

    .panel-resizer {
      display: none;
    }

    .panel {
      max-height: none;
      border-left: 0;
      border-top: 1px solid #2a3636;
    }
  }
</style>
