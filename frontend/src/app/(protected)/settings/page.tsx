"use client";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { ProvidersSection } from "@/components/settings/providers-section";
import { McpServersSection } from "@/components/settings/mcp-servers-section";
import { SkillsSection } from "@/components/settings/skills-section";
import { ThemeSwitcher } from "@/components/settings/theme-switcher";
import { GeneralSection } from "@/components/settings/GeneralSection";
import { EmbeddingsSection } from "@/components/settings/EmbeddingsSection";
import { FileList } from "@/components/files/file-list";

export default function SettingsPage() {
  return (
    <Tabs defaultValue="providers">
      <TabsList>
        <TabsTrigger value="providers">LLM Providers</TabsTrigger>
        <TabsTrigger value="embeddings">Embeddings</TabsTrigger>
        <TabsTrigger value="files">Files</TabsTrigger>
        <TabsTrigger value="mcp-servers">MCP Servers</TabsTrigger>
        <TabsTrigger value="skills">Skills</TabsTrigger>
        <TabsTrigger value="general">General</TabsTrigger>
        <TabsTrigger value="appearance">Appearance</TabsTrigger>
      </TabsList>

      <TabsContent value="providers" className="mt-4">
        <ProvidersSection />
      </TabsContent>

      <TabsContent value="embeddings" className="mt-4">
        <EmbeddingsSection />
      </TabsContent>

      <TabsContent value="files" className="mt-4">
        <FileList />
      </TabsContent>

      <TabsContent value="mcp-servers" className="mt-4">
        <McpServersSection />
      </TabsContent>

      <TabsContent value="skills" className="mt-4">
        <SkillsSection />
      </TabsContent>

      <TabsContent value="general" className="mt-4">
        <GeneralSection />
      </TabsContent>

      <TabsContent value="appearance" className="mt-4">
        <ThemeSwitcher />
      </TabsContent>
    </Tabs>
  );
}
