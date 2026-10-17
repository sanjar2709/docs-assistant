<template>
	<div class="min-h-screen flex-center p-4 bg-gradient-to-br from-primary-50 via-white to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
		<div class="w-full max-w-[400px]">
			<div class="flex items-center justify-center gap-2 mb-8 font-bold text-2xl">
				<img src="/favicon.svg" alt="" class="w-9 h-9" />
				<span>Docs Assistant</span>
			</div>
			<div class="bg-white dark:bg-slate-900 rounded-2xl shadow-xl shadow-slate-200/50 dark:shadow-none border border-slate-200 dark:border-slate-800 p-6 sm:p-8">
				<slot />
			</div>
		</div>
	</div>
</template>
