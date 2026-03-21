"use client";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ProvidersSection } from "@/components/settings/providers-section";
import { ThemeSwitcher } from "@/components/settings/theme-switcher";

export default function SettingsPage() {
  return (
    <Tabs defaultValue="providers">
      <TabsList>
        <TabsTrigger value="providers">LLM Providers</TabsTrigger>
        <TabsTrigger value="appearance">Appearance</TabsTrigger>
      </TabsList>

      <TabsContent value="providers" className="mt-4">
        <ProvidersSection />
      </TabsContent>

      <TabsContent value="appearance" className="mt-4">
        <ThemeSwitcher />
      </TabsContent>
    </Tabs>
  );
}
